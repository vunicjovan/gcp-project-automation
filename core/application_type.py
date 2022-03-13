from enum import Enum


class ApplicationType(Enum):
    """
    Enumerates types of applications to be added to Firebase.
    """

    ANDROID, IOS = range(2)
