from __future__ import annotations
from datetime import datetime, timedelta
from database.db import get_session
from database.models import Campaign, CampaignRecipient
from services.auth_service import auth_service


class CampaignController:

    def get_recent_recipient_ids(self, days: int = 7) -> set[int]:
        """Customer IDs that received a marketing message in the last *days* days."""
        cutoff = datetime.now() - timedelta(days=days)
        session = get_session()
        try:
            rows = (
                session.query(CampaignRecipient.customer_id)
                .join(Campaign)
                .filter(
                    Campaign.sent_at >= cutoff,
                    CampaignRecipient.status == "sent",
                    CampaignRecipient.customer_id.isnot(None),
                )
                .all()
            )
            return {r[0] for r in rows}
        finally:
            session.close()

    def send_campaign(
        self,
        message: str,
        customers: list,
        skip_ids: set[int] | None = None,
    ) -> tuple[int, int, int, int]:
        """
        Send *message* to all customers via WhatsApp.
        Customers whose IDs are in *skip_ids* are recorded as 'skipped'.
        Returns (campaign_id, sent, failed, skipped).
        """
        from services.notification_service import notification_service
        skip_ids = set(skip_ids or [])

        session = get_session()
        try:
            campaign = Campaign(
                message=message,
                sent_by=auth_service.current_user.username if auth_service.current_user else None,
            )
            session.add(campaign)
            session.flush()

            sent = failed = skipped = 0
            for c in customers:
                name = f"{c.name} {c.surname}"
                if c.id in skip_ids:
                    session.add(CampaignRecipient(
                        campaign_id=campaign.id,
                        customer_id=c.id,
                        customer_name=name,
                        phone=c.phone,
                        status="skipped",
                    ))
                    skipped += 1
                    continue

                ok = notification_service.send_message(c.phone, message) if c.phone else False
                session.add(CampaignRecipient(
                    campaign_id=campaign.id,
                    customer_id=c.id,
                    customer_name=name,
                    phone=c.phone,
                    status="sent" if ok else "failed",
                ))
                if ok:
                    sent += 1
                else:
                    failed += 1

            campaign_id = campaign.id
            session.commit()
            return campaign_id, sent, failed, skipped
        finally:
            session.close()

    def get_all(self) -> list[Campaign]:
        session = get_session()
        try:
            campaigns = (
                session.query(Campaign)
                .order_by(Campaign.sent_at.desc())
                .all()
            )
            for c in campaigns:
                session.expunge(c)
            return campaigns
        finally:
            session.close()

    def get_recipients(self, campaign_id: int) -> list[CampaignRecipient]:
        session = get_session()
        try:
            recips = (
                session.query(CampaignRecipient)
                .filter_by(campaign_id=campaign_id)
                .order_by(CampaignRecipient.customer_name)
                .all()
            )
            for r in recips:
                session.expunge(r)
            return recips
        finally:
            session.close()

    def count_recipients(self, campaign_id: int) -> dict[str, int]:
        """Returns {'sent': N, 'failed': N, 'skipped': N}."""
        session = get_session()
        try:
            rows = (
                session.query(CampaignRecipient.status,
                              session.query(CampaignRecipient).filter_by(
                                  campaign_id=campaign_id,
                              ).count)
                .filter_by(campaign_id=campaign_id)
                .all()
            )
            counts: dict[str, int] = {"sent": 0, "failed": 0, "skipped": 0}
            for r in session.query(CampaignRecipient).filter_by(campaign_id=campaign_id).all():
                counts[r.status] = counts.get(r.status, 0) + 1
            return counts
        finally:
            session.close()


campaign_controller = CampaignController()
