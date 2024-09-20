from flask_sqlalchemy import SQLAlchemy
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

db = SQLAlchemy()

class Data(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    method = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    card_num = db.Column(db.String(20), default='')
    date = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Data {self.name}>"

class BlockchainLog(db.Model):
    id = db.Column(db.Integer, primary_key=True, default=1)
    blockchain = db.Column(db.JSON, default=list)

    @classmethod
    def load_blockchain(cls):
        instance = cls.query.get(1)
        if instance is None:
            instance = cls(id=1, blockchain=[])
            db.session.add(instance)
            db.session.commit()
        return instance.blockchain

    @classmethod
    def save_blockchain(cls, blockchain):
        instance = cls.query.get(1)
        if not instance:
            instance = cls(id=1, blockchain=blockchain)
            db.session.add(instance)
        else:
            instance.blockchain = blockchain
        db.session.commit()

    def __repr__(self):
        return f"<BlockchainLog with {len(self.blockchain)} blocks>"

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    public_key = db.Column(db.Text, nullable=True)
    private_key = db.Column(db.Text, nullable=True)

    def save(self):
        if not self.public_key or not self.private_key:
            private_key, public_key = self.generate_key_pair(self.password.encode())
            self.private_key = private_key.decode('utf-8')
            self.public_key = public_key.decode('utf-8')
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def generate_key_pair(password: bytes):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=512,
            backend=default_backend()
        )
        public_key = private_key.public_key()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'some_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(password)

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(key)
        )

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return private_pem, public_pem

class VolunteerProject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<VolunteerProject {self.title}>"

class Volunteer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('volunteer_project.id'), nullable=False)
    project = db.relationship('VolunteerProject', backref=db.backref('volunteers', lazy=True))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<Volunteer {self.name} for {self.project.title}>"
