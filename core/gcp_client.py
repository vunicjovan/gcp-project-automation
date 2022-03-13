import base64
import json
import logging
import os
import plistlib
import time

import requests

# Basic log message configuration
from application_type import ApplicationType
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from requests.adapters import HTTPAdapter, Retry
from statics import FIREBASE_BASE_URL, GCP_CRM_BASE_URL, SCOPES, TOKEN_PATH

logging.basicConfig(
    level=logging.DEBUG,
    format="gcp-automated-setup - %(levelname)s - %(asctime)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


class GCPClient:
    """
    Represents a client for communication with Google Cloud Platform and Firebase APIs.

    Currently supported operations:
        * Authorization / Authentication
        * Creation of a Google Cloud Platform project
        * Addition of Firebase to an existing Google Cloud Platform project
        * Addition of Android application to an existing Firebase project
        * Addition of iOS application to an existing Firebase project
        * Download of configuration artifact associated with an existing Android application
        * Download of configuration artifact associated with an existing iOS application
    """

    def _obtain_credentials(self, credentials_file):
        """
        Obtains access and refresh token information from Google Cloud Platform
        based on provided credentials (in a form of JSON file).

        The code is based on the official Google Cloud Platform documentation.
        Reference: https://developers.google.com/docs/api/quickstart/python

        :param credentials_file: Path to the credentials JSON file obtained from GCP
        :type credentials_file: str
        """

        credentials = None

        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_PATH):
            credentials = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file,
                    SCOPES,
                )

                credentials = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(TOKEN_PATH, "w") as token:
                token.write(credentials.to_json())

        self.credentials = credentials

    def __init__(self, credentials_file):
        """
        Initializes Google Cloud Platform client by setting the access / refresh
        token info based on the provided credentials obtained from Google Cloud Platform
        in a form of a JSON file.

        :param credentials_file: Path to the credentials JSON file obtained from GCP
        :type credentials_file: str
        """

        self._obtain_credentials(credentials_file)

    def _execute_api_call(self, url, method, query_params=None, body=None):
        """
        Performs an HTTP request to the specified URL based on provided HTTP
        method name and (optionally) query parameters and/or request body.

        :param url: Target URL
        :type url: str
        :param method: HTTP method name (POST, GET, PUT, etc.)
        :type method: str
        :param query_params: Query parameters
        :type query_params: dict
        :param body: Request body
        :type body: dict
        :return: HTTP Response
        :rtype: requests.Response
        """

        # Each request sent to Google Cloud Platform / Firebase API requires
        # auth (bearer token) and content-type headers
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json",
        }

        # Consequence of the specified Content-Type header (application/json)
        body = json.dumps(body) if body else None

        try:
            logging.debug(
                f"Performing HTTP request:\n"
                f"Headers: {headers}\n"
                f"URL: {url}\n"
                f"Query parameters: {query_params}\n"
                f"Request body: {body}\n"
                f"..."
            )

            # Opens up a session with maximum of 10 retries and increases waiting
            # time for each retry automatically
            s = requests.Session()

            retries = Retry(
                total=10,
                backoff_factor=1,
                status_forcelist=[400, 403, 404, 500, 502, 503, 504],
                method_whitelist=False,  # Needs to be set to False, so it retries for POST also
            )

            # Binds the retry-mechanism to API calls sent to URLs starting with HTTPS
            s.mount("https://", HTTPAdapter(max_retries=retries))

            return s.request(
                method=method,
                url=url,
                params=query_params,
                data=body,
                headers=headers,
            )
        except requests.exceptions.RequestException as err:
            logging.warning(
                f"HTTP request:\n"
                f"Headers: {headers}\n"
                f"URL: {url}\n"
                f"Query parameters: {query_params}\n"
                f"Request body: {body}\n"
                f"has failed"
            )
            logging.exception(err)

    def create_gcp_project(self, gcp_project_id, project_name=None):
        """
        Creates a new Google Cloud Platform project configured with the
        help of the provided keyword arguments.

        Reference:
        https://cloud.google.com/resource-manager/reference/rest/v3/projects/create

        :param gcp_project_id: Google Cloud Platform project ID
        :type gcp_project_id: str
        :param project_name: Google Cloud Platform project name (optional)
        :type project_name: str
        :return: HTTP Response object
        :rtype: requests.Response
        """

        body = dict(projectId=gcp_project_id)

        if project_name:
            body["displayName"] = project_name

        logging.info(f"Creating Google Cloud Platform project: {body} ...")

        return self._execute_api_call(
            url=f"{GCP_CRM_BASE_URL}/projects",
            method="post",
            body=body,
        )

    def add_firebase_to_gcp_project(self, gcp_project_id):
        """
        Adds Firebase functionality to an existing Google Cloud Platform project,
        i.e. creates a new Firebase project and binds it with an existing Google
        Cloud Platform project based on the provided project ID.

        Reference:
        https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects/addFirebase

        :param gcp_project_id: Google Cloud Platform project ID
        :type gcp_project_id: str
        :return: HTTP Response object
        :rtype: requests.Response
        """

        logging.info(
            f"Adding Firebase functionality to a Google Cloud "
            f"Platform project {gcp_project_id} ..."
        )

        return self._execute_api_call(
            url=f"{FIREBASE_BASE_URL}/projects/{gcp_project_id}:addFirebase",
            method="post",
            body={},
        )

    def _fetch_firebase_project(self, fb_project_id):
        """
        Fetches a Firebase project with the specified ID.

        Reference:
        https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects/get

        :param fb_project_id: Firebase project ID
        :type fb_project_id: str
        :return: HTTP Response object
        :rtype: requests.Response
        """

        logging.info(f"Fetching info for the Firebase project {fb_project_id} ...")

        return self._execute_api_call(
            url=f"{FIREBASE_BASE_URL}/projects/{fb_project_id}",
            method="get",
        )

    def add_app_to_firebase_project(
        self,
        fb_project_id,
        package_name,
        app_name=None,
        store_id=None,
        app_type=ApplicationType.ANDROID,
    ):
        """
        Adds an Android/iOS application to an existing Firebase project.

        References:
            * https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.androidApps/create
            * https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.iosApps/create

        :param fb_project_id: Firebase project ID
        :type fb_project_id: str
        :param package_name: Android package name / iOS bundle ID
        :type package_name: str
        :param app_name: Name of the Android/iOS application (optional)
        :type app_name: str
        :param store_id: ID of the App Store (optional)
        :type store_id: str
        :param app_type: Type of application (Android, iOS)
        :type app_type: ApplicationType
        :return: Application ID
        :rtype: str
        """

        fb_seconds = 1

        # A conditional-waiting mechanism which ensures that the previously
        # created Firebase project is completely set-up, else applications
        # cannot be added to it
        while True:
            fb_project = self._fetch_firebase_project(fb_project_id).json()

            if (
                fb_project
                and fb_project.get("projectId") == fb_project_id
                and fb_project.get("state") == "ACTIVE"
            ):
                break

            time.sleep(fb_seconds)
            fb_seconds = fb_seconds + 1

        target_url = f"{FIREBASE_BASE_URL}/projects/{fb_project_id}"

        # Handle the URL and body parts according to type of the application to be added
        if app_type == ApplicationType.ANDROID:
            target_url = target_url + "/androidApps"
            body = dict(packageName=package_name)
        else:
            target_url = target_url + "/iosApps"
            body = dict(bundleId=package_name)

            if store_id:
                body["appStoreId"] = store_id

        if app_name:
            body["displayName"] = app_name

        logging.info(
            f"Adding {app_type.name} application {body} to the Firebase project {fb_project_id} ..."
        )

        self._execute_api_call(url=target_url, method="post", body=body)

        # A conditional-waiting mechanism which ensures that the previously
        # created application is completely set-up, so its ID can be properly fetched
        apps = None
        apps_seconds = 0

        while not apps:
            time.sleep(apps_seconds)

            apps = self._fetch_apps_of_firebase_project(
                fb_project_id=fb_project_id,
                app_type=app_type,
            ).json()

            apps_seconds = apps_seconds + 1

        # Fetch application ID as the ID of the first application of the
        # given application type within the specified Firebase project
        first_app = apps.get("apps")[0]
        app_id = first_app.get("appId")

        return app_id

    def _fetch_apps_of_firebase_project(
        self,
        fb_project_id,
        app_type=ApplicationType.ANDROID,
    ):
        """
        Fetches all the Android or iOS applications within a Firebase project
        with specified ID.

        References:
        https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.androidApps/list
        https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.iosApps/list

        :param fb_project_id: Firebase project ID
        :type fb_project_id: str
        :param app_type: Type of applications to be fetched (Android, iOS)
        :type app_type: ApplicationType
        :return: HTTP Response object
        :rtype: requests.Response
        """

        logging.info(
            f"Fetching {app_type} applications within the Firebase project {fb_project_id} ..."
        )

        return self._execute_api_call(
            url=f"{FIREBASE_BASE_URL}/projects/{fb_project_id}/{app_type.name.lower()}Apps",
            method="get",
        )

    def download_app_configuration(
        self,
        fb_project_id,
        app_id,
        app_type=ApplicationType.ANDROID,
        path=None,
    ):
        """
        Downloads locally configuration file for Android/iOS application.

        References:
            * https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.androidApps/getConfig
            * https://firebase.google.com/docs/projects/api/reference/rest/v1beta1/projects.iosApps/getConfig

        :param fb_project_id: Firebase project ID
        :type fb_project_id: str
        :param app_id: Application ID
        :type app_id: str
        :param app_type: Type of application (Android, iOS)
        :type app_type: ApplicationType
        :param path: Path marking where the configuration file will be downloaded
        :type path: str
        """

        # Handle the empty paths and paths ending/not ending with slash ('/')
        path = path if path else ""
        path = path if (path.endswith("/") or path == "") else f"{path}/"

        url_part = "androidApps" if app_type == ApplicationType.ANDROID else "iosApps"

        logging.info(
            f"Fetching configuration info for {app_type.name.lower()} "
            f"application {app_id} ..."
        )

        r = self._execute_api_call(
            url=f"{FIREBASE_BASE_URL}/projects/{fb_project_id}/{url_part}/{app_id}/config",
            method="get",
        ).json()

        logging.info(
            f"Decoding configuration info for {app_type.name.lower()} "
            f"application {app_id} ..."
        )

        # Decode the Base64-encoded content of the configuration artifact
        decoded_config = base64.b64decode(r.get("configFileContents")).decode("utf8")

        # Use the file name and extension provided with response from API
        file_path = f"{path}{r.get('configFilename')}"

        logging.info(
            f"Saving configuration info for {app_type.name.lower()} "
            f"application {app_id} to {file_path} ..."
        )

        # Save configuration artifact locally according to type of the application
        if app_type == ApplicationType.ANDROID:
            with open(file_path, "w", encoding="utf-8") as outfile:
                decoded_json = json.loads(decoded_config)
                json.dump(decoded_json, outfile, ensure_ascii=False, indent=4)
        else:
            with open(file_path, "wb") as outfile:
                decoded_plist = plistlib.loads(str.encode(decoded_config))
                plistlib.dump(decoded_plist, outfile)

        logging.info(
            f"Configuration info for {app_type.name.lower()} "
            f"application {app_id} saved as {file_path}"
        )
