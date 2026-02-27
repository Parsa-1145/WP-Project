# WP-Project Backend

This is the backend for the WP-Project web application, developed using Django. It provides APIs and handles data management for the frontend application.

# Quick Start (Developmet)

To get started with the project, follow these steps:
1. **Install the package manager(PDM)**
    ```bash
    pip install pdm
    ```
2. **Install dependencies**
    ```bash
    pdm install --dev
    ```
3. **Environment Variables**
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with your configuration. Fill the *DJANGO_SECRET_KEY* and *DATABASE_URL*
4. **Run Migrations**
    ```bash
    pdm run python manage.py migrate
    pdm run python manage.py makemigrations
    ```
5. **Start the Development Server**
    ```bash
    pdm run python manage.py runserver
    ```

---

## Custom Permissions

Custom permissions are defined in model `Meta` classes. Below is the full list and **where each permission is checked** in the codebase.

### `cases` app

| Model | Permission (codename) | Human name | Where it is checked |
|-------|------------------------|------------|----------------------|
| **Case** | `investigate_on_case` | Can investigate on a case | `cases/views.py`: dashboard modules (ASSIGNED_CASES); `investigation/permissions.py`: board access. Submission stage target: `cases/submissiontypes.py` (evidence submission). |
| **Case** | `supervise_case` | Can supervise a case | `cases/views.py`: dashboard modules (ASSIGNED_CASES). Submission stage target: `cases/submissiontypes.py` (case staffing). |
| **Case** | `add_case_acceptance_submission` | Can add a submission to find a lead_detective and a supervisor for a case | `submissions/submissiontypes/classes.py`: `create_permissions` for case staffing submission type (`case.add_case_acceptance_submission` in code). |
| **Case** | `assess_suspect_guilt` | Can assess whether suspects are guilty or not guilty | Submission stage target: `cases/submissiontypes.py` (guilt assessment). |
| **Case** | `approve_suspect_guilt_assessment` | Can approve suspect guilt assessments in critical cases | Submission stage target: `cases/submissiontypes.py` (critical-case guilt approval). |
| **Case** | `jury_case` | Can judge a case | `cases/views.py`: dashboard modules (JURY); `GetTrialCases.get_queryset()`; verdict submission view (only users with this permission can access trial cases and submit verdicts). |
| **Complaint** | `complaint_initial_approve` | Can approve complaint submissions | Submission stage target: `cases/submissiontypes.py` (complaint workflow). |
| **Complaint** | `complaint_final_approve` | Can approve the approval of a complaint submissions | Submission stage target: `cases/submissiontypes.py` (complaint workflow). |
| **CrimeScene** | `approve_crime_scene` | Can approve crime scene | `cases/submissiontypes.py`: crime scene submission (creator with this permission can auto-approve); submission stage target for crime scene approval. |

### `evidence` app

| Model | Permission (codename) | Human name | Where it is checked |
|-------|------------------------|------------|----------------------|
| **Evidence** | `view_evidence` | (Django default) | `evidence/views.py`: evidence list/detail queryset. |
| **BioEvidence** | `can_approve_bioevidence` | Can Approve bio evidence | `cases/views.py`: dashboard modules (AUTOPSY). Submission stage target: `evidence/submissiontypes.py`. |

### `payments` app

| Model | Permission (codename) | Human name | Where it is checked |
|-------|------------------------|------------|----------------------|
| **BailRequest** | `can_approve_bail_request` | Can approve bail requests | Submission stage target: `payments/submissiontypes.py` (bail approval stage). |
| **DataForReward** | `can_approve_data_reward` | Can approve data for reward submissions | Submission stage target: `payments/submissiontypes.py` (data-for-reward approval stage). |

---

## Police ranks and groups

To create Django groups for each police rank and assign the correct permissions, run:

```bash
pdm run python manage.py setup_police_ranks
```

This command creates groups and permissions according to the رده های پلیس (Police Ranks) specification. See the command help for the mapping of ranks to permissions.
