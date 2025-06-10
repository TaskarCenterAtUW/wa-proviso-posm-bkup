'''
Data object example
{
    "osw_validity": true,
    "tdei_job_id": "5830",
    "nodes_validity": false,
    "edges_validity": true,
    "long_sidewalks_exist": false,
    "long_sidealks_changeset": null,
    "osw_error_file": null,
    "nodes_error_file": "https://provisodevstorage.blob.core.windows.net/osw-jobs/0eefc1e4-9eec-4bcb-abaf-ec7f38be5c0d/problem.nodes.geojson",
    "edges_error_file": null,
    "can_retry": false,
    "zip_extraction": true,
    "zip_extraction_error": null,
    "upload_error": null
}
'''
class MCUploadReport:
    def __init__(self, data):
        self.osw_validity = data.get("osw_validity", False)
        self.tdei_job_id = data.get("tdei_job_id", "")
        self.nodes_validity = data.get("nodes_validity", False)
        self.edges_validity = data.get("edges_validity", False)
        self.long_sidewalks_exist = data.get("long_sidewalks_exist", False)
        self.long_sidealks_changeset = data.get("long_sidealks_changeset", None)
        self.osw_error_file = data.get("osw_error_file", None)
        self.nodes_error_file = data.get("nodes_error_file", None)
        self.edges_error_file = data.get("edges_error_file", None)
        self.can_retry = data.get("can_retry", False)
        self.zip_extraction = data.get("zip_extraction", True)
        self.zip_extraction_error = data.get("zip_extraction_error", None)
        self.upload_error = data.get("upload_error", None)
    def get_status(self):
        # if osw_validity is false, return "Invalid OSW"
        if not self.osw_validity:
            return False, "Invalid OSW"
        if self.long_sidewalks_exist:
            return False, "Long sidewalks exist"
        if self.upload_error:
            return False, "Upload error: " + self.upload_error
        if self.tdei_job_id:
            return True, "Upload successful"
        pass