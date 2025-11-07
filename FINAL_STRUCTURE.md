# External Connectivity Microservice - Final Structure

## ✅ What This Microservice Does

**Acts as a PROXY/INTERMEDIARY** between internal services and external centralizer (Govcarpeta API).

**Does NOT store business data**, only **communication traces**.

---

## 📁 Final Clean Structure

```
project_connectivity/
├── apps/
│   ├── citizen_validation/          # FUNCTION #1
│   │   ├── models.py                # CitizenValidationTrace
│   │   ├── services.py              # CitizenValidationService
│   │   ├── views.py                 # CitizenValidationView (REST)
│   │   ├── external_views.py        # check_citizen_exists (for auth-microservice)
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   └── tests.py
│   │
│   ├── citizen_registration/        # FUNCTION #2
│   │   ├── models.py                # CitizenRegistrationTrace
│   │   ├── services.py              # CitizenRegistrationService
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── tests.py
│   │   └── management/commands/
│   │       └── consume_auth_events.py    # ✅ NEEDED: RabbitMQ consumer
│   │
│   └── document_authentication/     # FUNCTION #3
│       ├── models.py                # DocumentAuthenticationTrace
│       ├── services.py              # DocumentAuthenticationService
│       ├── admin.py
│       ├── apps.py
│       ├── tests.py
│       └── management/commands/
│           └── consume_document_auth.py  # ✅ NEEDED: RabbitMQ consumer
│
├── infrastructure/
│   ├── auth/                        # OAuth2 JWT validation
│   │   ├── oauth2_validator.py
│   │   └── __init__.py
│   ├── external_apis/               # External API clients
│   │   ├── base_client.py
│   │   ├── govcarpeta_client.py
│   │   └── __init__.py
│   └── rabbitmq/                    # RabbitMQ integration
│       ├── producer.py
│       ├── consumer.py
│       └── __init__.py
│
├── settings/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── requirements/
│   ├── base.txt
│   └── dev.txt
│
├── monitoring/                      # ✅ NEEDED: Prometheus & Grafana
│   ├── prometheus/
│   └── grafana/
│
├── scripts/
│   └── test_jwt_validation.py       # ✅ NEEDED: JWT testing utility
│
├── docker-compose.yml
├── Dockerfile
├── .env.example
├── manage.py
├── pytest.ini                       # ✅ NEEDED: Test configuration
├── .flake8                          # ✅ NEEDED: Linting
├── pyproject.toml                   # ✅ NEEDED: Black, isort config
├── sonar-project.properties         # ✅ NEEDED: Code quality
└── PROJECT_STRUCTURE.md
```

---

## 🎯 What Each Component Does

### Apps (3 Core Functions)

#### 1. `citizen_validation/`
**Purpose**: Query external API to check if citizen exists

**Files**:
- `models.py` - CitizenValidationTrace (stores: citizen_id, status, timestamp)
- `services.py` - CitizenValidationService.validate_citizen()
- `views.py` - POST /api/v1/citizen/validation/check/ (internal)
- `external_views.py` - GET /api/external/citizen/:id (for auth-microservice)

**No REST consumer needed** - responds to direct HTTP requests

---

#### 2. `citizen_registration/`
**Purpose**: Forward registration requests to external API

**Files**:
- `models.py` - CitizenRegistrationTrace (stores: message_id, citizen_id, status)
- `services.py` - CitizenRegistrationService.process_auth_registration_event()
- `management/commands/consume_auth_events.py` - **RabbitMQ consumer** ✅

**Why management/commands?**
- Django's way to create custom commands
- Allows: `python manage.py consume_auth_events`
- Runs as a long-running process listening to RabbitMQ

---

#### 3. `document_authentication/`
**Purpose**: Forward document authentication to external API

**Files**:
- `models.py` - DocumentAuthenticationTrace (stores: citizen_id, document_title, status)
- `services.py` - DocumentAuthenticationService.process_authentication_request()
- `management/commands/consume_document_auth.py` - **RabbitMQ consumer** ✅

**Why management/commands?**
- Same as above - custom Django command
- Allows: `python manage.py consume_document_auth`
- Runs as a long-running process listening to RabbitMQ

---

### Infrastructure

#### `infrastructure/auth/`
- OAuth2 JWT validation for auth-microservice
- Validates tokens locally (no network call)

#### `infrastructure/external_apis/`
- HTTP clients for Govcarpeta API
- Retry logic, timeout handling

#### `infrastructure/rabbitmq/`
- Producer: Publish events
- Consumer: Base class for consumers

---

### Configuration Files (All Needed)

#### For Development
- `.env.example` - Environment variables template
- `docker-compose.yml` - Local services (MariaDB, Redis, RabbitMQ)
- `pytest.ini` - Test configuration

#### For Code Quality
- `.flake8` - Linting rules
- `pyproject.toml` - Black (formatter), isort (imports), coverage
- `sonar-project.properties` - SonarCloud integration

#### For Production
- `Dockerfile` - Production image
- `monitoring/` - Prometheus & Grafana configs

---

## 🗑️ What Was Removed

### Deleted (Unnecessary)
- ❌ `apps/authentication/` - Not needed (using Django's built-in JWT)
- ❌ `create_service_account.py` - Utility, not core
- ❌ `create_service_accounts.py` - Utility, not core
- ❌ `test_affiliation_endpoint.py` - Old test file
- ❌ `test_api_endpoints.py` - Old test file
- ❌ Empty `views.py` files in citizen_registration and document_authentication

### Renamed (For Clarity)
- `apps/affiliation/` → `apps/citizen_validation/`
- `apps/core/` → `apps/citizen_registration/`
- `apps/documents/` → `apps/document_authentication/`
- `AffiliationCheck` → `CitizenValidationTrace`
- `RegisteredCitizen` → `CitizenRegistrationTrace`
- `DocumentAuthentication` → `DocumentAuthenticationTrace`

---

## 🚀 How to Run

### Start Web Service
```bash
python manage.py runserver
```

### Start Consumers (in separate terminals)
```bash
# Terminal 1: Auth events
python manage.py consume_auth_events

# Terminal 2: Document authentication
python manage.py consume_document_auth
```

### Or Use Docker Compose
```bash
docker-compose up
```

---

## 📊 Database Tables (Traceability Only)

### `citizen_validation_traces`
```sql
citizen_id                  VARCHAR(50)
status                      VARCHAR(20)  -- EXISTS, NOT_EXISTS, ERROR
requested_at                TIMESTAMP
external_api_status_code    INT
error_message               TEXT
```

### `citizen_registration_traces`
```sql
message_id                  UUID         -- For idempotency
id_citizen                  BIGINT
status                      VARCHAR(20)  -- PENDING, SENT, FAILED, ERROR
received_at                 TIMESTAMP
sent_at                     TIMESTAMP
external_api_status_code    INT
external_api_response       JSON
error_message               TEXT
```

### `document_authentication_traces`
```sql
id_citizen                  BIGINT
document_title              VARCHAR(200)
status                      VARCHAR(20)  -- PENDING, SENT, FAILED, ERROR
auth_success                BOOLEAN
received_at                 TIMESTAMP
sent_at                     TIMESTAMP
event_published_at          TIMESTAMP
external_api_status_code    INT
error_message               TEXT
```

---

## ✅ Summary

**Clean, focused structure with:**
- 3 apps for 3 core functions
- Clear, descriptive names
- Only communication traces (no business data)
- Management commands for RabbitMQ consumers
- All necessary config files for production
- No unnecessary utilities or empty files

**Everything that remains is NEEDED for the 3 core functions.**
