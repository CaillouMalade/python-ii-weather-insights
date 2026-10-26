"""Convenient circuit centres, not surveyed racing-line geometry."""
from .models import Location

TRACKS = {
    "portimao": Location("Portimão", 37.2319, -8.6267, "Europe/Lisbon"),
    "nogaro": Location("Nogaro", 43.7699, -0.0327, "Europe/Paris"),
    "spa": Location("Spa-Francorchamps", 50.4372, 5.9714, "Europe/Brussels"),
    "paul-ricard": Location("Paul Ricard", 43.2506, 5.7917, "Europe/Paris"),
    "le-mans": Location("Le Mans", 47.9497, 0.2058, "Europe/Paris"),
    "barcelona": Location("Barcelona-Catalunya", 41.5700, 2.2611, "Europe/Madrid"),
}
