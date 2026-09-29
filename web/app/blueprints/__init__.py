def register_blueprints(app):
    """Registra todos os blueprints. Cresce a cada tarefa que adiciona telas."""
    from app.blueprints import main, order, search

    app.register_blueprint(main.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(order.bp)
