from __future__ import annotations
from datetime import datetime, timedelta
from database.db import get_session
from database.models import Campaign, CampaignRecipient
from services.auth_service import auth_service
from sqlalchemy import func


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

    def get_last_campaign_date(self, customer_id: int) -> datetime | None:
        """Most recent campaign sent_at for a customer (status=sent)."""
        session = get_session()
        try:
            row = (
                session.query(Campaign.sent_at)
                .join(CampaignRecipient, CampaignRecipient.campaign_id == Campaign.id)
                .filter(
                    CampaignRecipient.customer_id == customer_id,
                    CampaignRecipient.status == "sent",
                )
                .order_by(Campaign.sent_at.desc())
                .first()
            )
            return row[0] if row else None
        finally:
            session.close()

    def send_campaign(
        self,
        message: str,
        customers: list,
        skip_ids: set[int] | None = None,
        name: str | None = None,
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
                name=name,
                message=message,
                sent_by=auth_service.current_user.username if auth_service.current_user else None,
            )
            session.add(campaign)
            session.flush()

            sent = failed = skipped = 0
            for c in customers:
                full_name = f"{c.name} {c.surname}"
                if c.id in skip_ids:
                    session.add(CampaignRecipient(
                        campaign_id=campaign.id,
                        customer_id=c.id,
                        customer_name=full_name,
                        phone=c.phone,
                        status="skipped",
                    ))
                    skipped += 1
                    continue

                ok = notification_service.send_message(c.phone, message) if c.phone else False
                session.add(CampaignRecipient(
                    campaign_id=campaign.id,
                    customer_id=c.id,
                    customer_name=full_name,
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

    def get_all_with_counts(self) -> list[tuple]:
        """Returns list of (Campaign, sent, failed, skipped) using 2 queries instead of N+1."""
        session = get_session()
        try:
            campaigns = (
                session.query(Campaign)
                .order_by(Campaign.sent_at.desc())
                .all()
            )
            if not campaigns:
                return []

            camp_ids = [c.id for c in campaigns]
            rows = (
                session.query(
                    CampaignRecipient.campaign_id,
                    CampaignRecipient.status,
                    func.count(CampaignRecipient.id),
                )
                .filter(CampaignRecipient.campaign_id.in_(camp_ids))
                .group_by(CampaignRecipient.campaign_id, CampaignRecipient.status)
                .all()
            )

            counts: dict[int, dict[str, int]] = {}
            for camp_id, status, cnt in rows:
                counts.setdefault(camp_id, {"sent": 0, "failed": 0, "skipped": 0})
                counts[camp_id][status] = cnt

            result = []
            for c in campaigns:
                session.expunge(c)
                c_counts = counts.get(c.id, {"sent": 0, "failed": 0, "skipped": 0})
                result.append((c, c_counts["sent"], c_counts["failed"], c_counts["skipped"]))
            return result
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
            counts: dict[str, int] = {"sent": 0, "failed": 0, "skipped": 0}
            for r in session.query(CampaignRecipient).filter_by(campaign_id=campaign_id).all():
                counts[r.status] = counts.get(r.status, 0) + 1
            return counts
        finally:
            session.close()


campaign_controller = CampaignController()
