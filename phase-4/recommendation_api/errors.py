"""Error handlers for the recommendation API."""

from __future__ import annotations

from flask import Flask, jsonify

from .schemas import ErrorResponse


def register_error_handlers(app: Flask) -> None:
    """Register JSON error handlers on the Flask app."""

    @app.errorhandler(400)
    def bad_request(exc: Exception):
        body = ErrorResponse(
            error="Bad request",
            details=[str(exc)],
        )
        return jsonify(body.to_dict()), 400

    @app.errorhandler(422)
    def validation_error(exc: Exception):
        body = ErrorResponse(
            error="Validation error",
            details=[str(exc)],
        )
        return jsonify(body.to_dict()), 422

    @app.errorhandler(500)
    def internal_error(exc: Exception):
        body = ErrorResponse(
            error="Internal server error",
            details=[],
        )
        return jsonify(body.to_dict()), 500
