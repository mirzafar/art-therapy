from sanic import Blueprint

from admin.api.districts import districts_bp
from admin.api.regions import regions_bp
from admin.api.tracks import tracks_bp
from admin.api.traffics import traffics_bp
from admin.api.users import users_bp

main_bp = Blueprint('main', url_prefix='/')

api_group = Blueprint.group(
    main_bp,
    users_bp,
    tracks_bp,
    regions_bp,
    districts_bp,
    traffics_bp,
    url_prefix='/api'
)
