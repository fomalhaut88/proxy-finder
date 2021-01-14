# proxy-finder

**proxy-finder** is a service that searches for HTTPS proxy in the net, checks
them and provides an API to list. It keeps the list actual by checking proxy
periodically. Each proxy has its own score that can be interpreted as a
probability to access the proxy, the value is estimated and being recalculated
by the algorithm in the service. Also there is an information about proxy
location.

The service is deployed here: https://proxy.fomalhaut.su/api/v1/

## API

### URLs

| URL | Method | Description | Request example |
|---|---|---|---|
| `/list` | GET | List of actual proxies. There are several GET parameters to manage the output. | https://proxy.fomalhaut.su/api/v1/list?format=plain&ordered=1&country=US&count=5&score=0.5 |
| `/geo/<host>` | GET | Geo information about the host. | https://proxy.fomalhaut.su/api/v1/geo/3.80.37.204 |
| `/check/<proxy>` | GET | Checks HTTPS proxy. | https://proxy.fomalhaut.su/api/v1/check/3.80.37.204:3128 |
| `/version` | GET | Shows version on the service. | https://proxy.fomalhaut.su/api/v1/version |
| `/licenses` | GET | Licenses used in the project. | https://proxy.fomalhaut.su/api/v1/licenses |

### GET parameters for `/list`

| Parameter | Description | Default | Example |
|---|---|---|---|
| `country` | Filter by country. The value must be two capital letters of the country code. | ` ` | `country=US` |
| `region` | Filter by region. | ` ` | `region=Virginia` |
| `city` | Filter by city. | ` ` | `city=Ashburn` |
| `count` | The number of proxies. `0` means all records. | `0` | `count=10` |
| `score` | The minimal score. `0.0` means all records. | `0.0` | `score=0.5` |
| `ordered` | Sort by score descendly. | ` ` | `ordered=1` |
| `format` | Output format (`plain` or `json`). | `json` | `format=plain` |

## Deployment

1. Clone the repository: `git clone --depth 1 https://github.com/fomalhaut88/proxy-finder.git`
2. Download and unzip free IP location database from here (in CSV): https://db-ip.com/db/download/ip-to-city-lite (note: on download you agree with the licensing terms on the page, keep it in mind)
3. Prepare binary geo database: `python manage.py prepare_geoip_db` (before using it, it is necessary to install Python 3.8, all the requirements from `requirements.txt` and to set environment variable *GEOIP_DB_PATH* to the desired path of the binary database)
4. Copy `docker-compose.yml` from `docker-compose-example.yml` and configure it
5. Configure Nginx using `docker/nginx.conf` as hint
6. Run docker-compose: `docker-compose up -d --build --remove-orphans`

## Licenses

Geo data is taken from https://db-ip.com/ under [Creative Commons Attribution 4.0 International License](http://creativecommons.org/licenses/by/4.0/).
