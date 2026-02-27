"""
Create Django groups for police ranks (رده های پلیس) and assign the correct
permissions according to the official role descriptions.

Ranks (from doc):
  1. کارآموز (Intern/Trainee) – initial filtering/validation of complaints; forward for case file creation
  2. پزشک قانونی (Forensic Doctor) – examine/confirm/reject biological and medical evidence
  3. افسر پلیس و افسر گشت (Police Officer / Patrol Officer) – field activities, report crimes, crime scene
  4. کارآگاه (Detective) – search evidence, deduce connections, identify suspects, assist interrogation
  5. گروهبان (Sergeant) – solve cases, arrest warrants, interrogate, assess guilt, report to Captain/Chief
  6. کاپیتان (Captain) – approve case files and forward to judiciary for trial
  7. رئیس پلیس (Police Chief) – in critical crimes can directly refer to judiciary (bypass Captain)
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


# (app_label, model (lowercase), codename)
def _perm(app_label: str, model: str, codename: str) -> tuple[str, str, str]:
    return (app_label, model, codename)


def get_permission(app_label: str, model: str, codename: str) -> Permission | None:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        return Permission.objects.get(content_type=ct, codename=codename)
    except (ContentType.DoesNotExist, Permission.DoesNotExist):
        return None


class Command(BaseCommand):
    help = (
        "Create groups for police ranks (رده های پلیس) and assign permissions. "
        "Idempotent: safe to run multiple times."
    )

    # group_name, display_name, list of _perm(app_label, model, codename)
    RANKS = [
        (
            "intern",
            "Intern",
            [
                _perm("cases", "complaint", "complaint_initial_approve"),
            ],
        ),
        (
            "coroner",
            "Coroner",
            [
                _perm("evidence", "bioevidence", "can_approve_bioevidence"),
            ],
        ),
        (
            "police_officer",
            "Police Officer",
            [
                _perm("cases", "crimescene", "approve_crime_scene"),
                _perm("cases", "case", "view_case"),
            ],
        ),
        (
            "detective",
            "Detective",
            [
                _perm("cases", "case", "view_case"),
                _perm("cases", "case", "investigate_on_case"),
            ],
        ),
        (
            "sergeant",
            "Sergeant",
            [
                _perm("cases", "case", "view_case"),
                _perm("cases", "case", "supervise_case"),
                _perm("cases", "case", "add_case_acceptance_submission"),
                _perm("cases", "case", "assess_suspect_guilt"),
            ],
        ),
        (
            "captain",
            "Captain",
            [
                _perm("cases", "case", "view_case"),
                _perm("cases", "case", "approve_suspect_guilt_assessment"),
                _perm("cases", "case", "jury_case"),
            ],
        ),
        (
            "police_chief",
            "Police Chief",
            [
                _perm("cases", "case", "view_case"),
                _perm("cases", "case", "approve_suspect_guilt_assessment"),
                _perm("cases", "case", "jury_case"),
                _perm("cases", "case", "supervise_case"),
                _perm("cases", "case", "assess_suspect_guilt"),
            ],
        ),
        (
            "judge",
            "Judge",
            [
                _perm("cases", "case", "view_case"),
                _perm("cases", "case", "jury_case"),
            ],
        )
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print what would be done, do not create or modify groups.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry run: no changes will be made."))

        def run():
            for group_name, display_name, perms in self.RANKS:
                self.stdout.write(f"Group: {display_name} ({group_name})")
                if dry_run:
                    exists = Group.objects.filter(name=group_name).exists()
                    self.stdout.write(
                        self.style.SUCCESS(f"  Would create group '{group_name}'")
                        if not exists
                        else f"  Group '{group_name}' already exists"
                    )
                else:
                    group, created = Group.objects.get_or_create(name=group_name)
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"  Created group '{group_name}'"))
                    else:
                        self.stdout.write(f"  Group '{group_name}' already exists")

                for app_label, model, codename in perms:
                    perm = get_permission(app_label, model, codename)
                    if perm is None:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Permission not found: {app_label}.{codename} (model={model})"
                            )
                        )
                        continue
                    if dry_run:
                        self.stdout.write(f"  Would assign: {perm.codename}")
                    else:
                        if group.permissions.filter(pk=perm.pk).exists():
                            self.stdout.write(f"  Already has: {perm.codename}")
                        else:
                            group.permissions.add(perm)
                            self.stdout.write(self.style.SUCCESS(f"  Assigned: {perm.codename}"))

        if dry_run:
            run()
        else:
            with transaction.atomic():
                run()
            self.stdout.write(self.style.SUCCESS("Done. Run with --dry-run to see planned changes."))
