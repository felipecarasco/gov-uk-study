def register_blueprints(app):
    """Registers every blueprint. Grows with each task that adds pages."""
    from app.blueprints import main, order, search

    app.register_blueprint(main.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(order.bp)
