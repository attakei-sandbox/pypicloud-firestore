from google.cloud import exceptions, firestore
from pypicloud.cache.base import ICache
from pypicloud.models import Package


__version__ = "0.1.0"


class FirestoreCache(ICache):
    """
        Caching database using Cloud Firestore
    """

    def __init__(self, request=None, db=None, collection_name=None, **kwargs):
        super().__init__(request, **kwargs)
        self.db = db
        self.collection_name = collection_name

    @classmethod
    def configure(cls, settings):
        kwargs = super().configure(settings)
        kwargs["db"] = firestore.Client()
        kwargs["collection_name"] = settings.pop("db.collection_name")
        return kwargs

    def fetch(self, filename):
        doc_ref = self.db.collection(self.collection_name).document(filename)
        try:
            snap = doc_ref.get()
            if not snap.exists:
                return None
            doc = snap.to_dict()
            return Package(
                doc["name"],
                doc["version"],
                filename,
                doc["last_modified"],
                doc["summary"],
                **doc["metadata"],
            )
        except exceptions.NotFound:
            return None

    def all(self, name):
        query = self.db.collection(self.collection_name).where("name", "==", name)
        pkgs = []
        for snap in query.stream():
            filename = snap.id
            doc = snap.to_dict()
            pkgs.append(Package(
                doc["name"],
                doc["version"],
                filename,
                doc["last_modified"],
                doc["summary"],
                **doc["metadata"],
            ))
        return pkgs

    def distinct(self):
        query = self.db.collection(self.collection_name)
        return list(set([
            doc.get("name")
            for doc in query.stream()
        ]))

    def clear(self, package):
        doc_ref = self.db.collection(self.collection_name).document(package.filename)
        doc_ref.delete()

    def clear_all(self):
        query = self.db.collection(self.collection_name)
        for doc in query.stream():
            doc.delete()

    def save(self, package):
        doc_ref = self.db.collection(self.collection_name).document(package.filename)
        doc_ref.set({
            "name": package.name,
            "version": package.version,
            "last_modified": package.last_modified,
            "summary": package.summary,
            "metadata": package.data,
        })
