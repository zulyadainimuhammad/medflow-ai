from collections.abc import Sequence

DEFAULT_ROLES: tuple[dict[str, str], ...] = (
    {
        "name": "Administrator",
        "description": "Full platform administration for MedFlow AI.",
    },
    {
        "name": "Doctor",
        "description": "Clinical requester for diagnostic workflows.",
    },
    {
        "name": "Laboratory Scientist",
        "description": "Laboratory workflow operator and verifier.",
    },
    {
        "name": "Radiographer",
        "description": "Radiology workflow operator and reporter.",
    },
    {
        "name": "Nurse",
        "description": "Patient readiness and movement coordinator.",
    },
    {
        "name": "Receptionist",
        "description": "Front-desk and appointment coordination role.",
    },
)


def get_default_role_seed_data() -> Sequence[dict[str, str]]:
    return DEFAULT_ROLES
