import json

from application_type import ApplicationType
from command_line_client import CommandLineClient
from gcp_client import GCPClient

if __name__ == "__main__":
    command_line_client = CommandLineClient()
    arguments = command_line_client.fetch_args()

    configuration_file = arguments.get("config_file")

    if configuration_file:
        with open(configuration_file) as f:
            arguments = json.load(f)

    gcp_client = GCPClient(credentials_file=arguments.get("auth"))

    project_id = arguments.get("gcp_project_id")

    # Step 1: Create a GCP project
    gcp_client.create_gcp_project(
        gcp_project_id=project_id,
        project_name=arguments.get("gcp_project_name"),
    )

    # Step 2: Add Firebase to the created GCP project
    gcp_client.add_firebase_to_gcp_project(gcp_project_id=project_id)

    # Step 3: Configure an Android app in the Firebase project
    android_app_id = gcp_client.add_app_to_firebase_project(
        fb_project_id=project_id,
        package_name=arguments.get("android_package"),
        app_name=arguments.get("android_app_name"),
    )

    # Step 4: Download the Android app configuration and store it locally as a JSON file
    gcp_client.download_app_configuration(
        fb_project_id=project_id,
        app_id=android_app_id,
        path=arguments.get("android_config_path"),
    )

    ios_bundle_id = arguments.get("ios_bundle_id")

    if ios_bundle_id:
        # Step 5 (optional): Configure an iOS app in the Firebase project
        ios_app_id = gcp_client.add_app_to_firebase_project(
            fb_project_id=project_id,
            package_name=ios_bundle_id,
            app_name=arguments.get("ios_app_name"),
            store_id=arguments.get("app_store_id"),
            app_type=ApplicationType.IOS,
        )

        # Step 6 (optional): Download the iOS configuration and store it locally as a JSON file
        gcp_client.download_app_configuration(
            fb_project_id=project_id,
            app_id=ios_app_id,
            app_type=ApplicationType.IOS,
            path=arguments.get("ios_config_path"),
        )
