"""WSGI entry point for EvidenceChain production deployment."""

from app import create_app

app = create_app()