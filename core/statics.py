# Base URLs used for each of the GCP/Firebase API calls
GCP_CRM_BASE_URL = "https://cloudresourcemanager.googleapis.com/v3"
FIREBASE_BASE_URL = "https://firebase.googleapis.com/v1beta1"

# Path for writing/reading of the GCP access/refresh token info
TOKEN_PATH = "token.json"

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

# Available command line arguments - keys: argument names; values: argument help descriptions
ARGUMENTS = dict(
    auth="Path to the credentials.json file obtained from Google Cloud Platform. "
    "Required if not using an external config file.",
    gcp_project_id="The unique, user-assigned id of the project. "
    "It must be 6 to 30 lowercase ASCII letters, digits, or hyphens. "
    "It must start with a letter. "
    "Trailing hyphens are prohibited. "
    "Required if not using an external config file. "
    "Example: my-test-project-123",
    gcp_project_name="A user-assigned display name of the project. "
    "When present it must be between 4 to 30 characters. "
    "Allowed characters are: lowercase and uppercase letters, numbers, hyphen, "
    "single-quote, double-quote, space, and exclamation point. "
    "Example: My Test Project",
    android_app_name="The user-assigned display name for the AndroidApp. "
    "Example: My Test App",
    android_package="The canonical package name of the Android app as would appear "
    "in the Google Play Developer Console. "
    "Required if not using an external config file. "
    "Example: com.test.app.project",
    ios_bundle_id="The canonical bundle ID of the iOS app as it would appear in the "
    "iOS AppStore. "
    "Must be specified when one of the following arguments is used: ios_app_name, "
    "app_store_id or ios_config_path."
    "Example: com.test.app.project",
    ios_app_name="The user-assigned display name for the IosApp. "
    "Example: My Test App",
    app_store_id="The automatically generated Apple ID assigned to the iOS app by "
    "Apple in the iOS App Store. "
    "Example: 123456789",
    android_config_path="Desired path for the configuration artifact associated with "
    "the previously created AndroidApp. Defaults to the current working directory. "
    "Example: C:/",
    ios_config_path="Desired path for the configuration artifact associated with the "
    "previously created IosApp. "
    "Defaults to the current working directory. "
    "Example: C:/",
    config_file="Path to an external configuration file represented in JSON format. "
    "This argument is self-sufficient and if it is specified, all the other "
    "arguments will be automatically omitted.",
)
