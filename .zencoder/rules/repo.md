---
description: Repository Information Overview
alwaysApply: true
---

# SOYA Agence Immobilière - Odoo Real Estate Module

## Summary
SOYA is a comprehensive real estate management system built as an Odoo 17 custom module. It provides complete property lifecycle management, offer tracking, and agent management for real estate agencies operating in Mali. The application includes property listings, offer management, communication features via Chatter integration, and activity tracking.

## Structure
- **custom_addons/soya_estate/**: Main Odoo module containing models, views, controllers, and business logic
- **config/**: Odoo configuration file with database and Redis settings
- **data/**: Runtime data directories for PostgreSQL and Odoo storage
- **legal_templates/**: Document templates for Mali-specific legal documents (contracts, invoices, receipts, property reports)
- **docker-compose.yml**: Multi-container orchestration for Odoo, PostgreSQL, and Redis services
- **logs/**: Application logs directory

## Language & Runtime
**Language**: Python  
**Framework**: Odoo 17.0  
**Module Version**: 17.0.1.0.0  
**Python Runtime**: Python 3 (via Docker)  
**Database**: PostgreSQL 16  
**Cache Layer**: Redis 7  

## Core Dependencies
**Odoo Base Modules**:
- `base`: Core Odoo framework
- `mail`: Chatter messaging and activity tracking features

**Infrastructure Dependencies**:
- PostgreSQL 16 (Database)
- Redis 7-alpine (Session storage and caching)
- Docker containers

## Main Models & Components

**Models**:
- `soya.property`: Main property/real estate record with tracking and mail threading
- `soya.property.type`: Property type classification
- `soya.property.offer`: Purchase/rental offer management

**Controllers**:
- Portal controllers for customer-facing interfaces
- Main application controllers

**Security**:
- Role-based access control (ir.model.access.csv)
- Domain-based security rules (soya_estate_rules.xml)

**Views**:
- Property list/form/kanban views (property_views.xml)
- Property type management (property_type_views.xml)
- Offer management (property_offer_views.xml)

**Wizards**:
- Close property wizard for property status transitions

## Installation & Usage

**Docker Setup**:
```bash
docker-compose up -d
```

**Access Points**:
- **Odoo Web Interface**: http://localhost:8069
- **PostgreSQL**: localhost:5434 (odoo user)
- **Redis**: localhost:6380

**Module Installation**:
Module automatically installed via docker-compose command: `odoo -c /etc/odoo/odoo.conf -u soya_estate`

**Configuration**:
```bash
# Odoo Configuration (config/odoo.conf)
- Database: soya_odoo_db
- Admin Password: admin
- Workers: 4
- Session Store: Redis
- Log Level: info
```

## Docker Configuration

**Services**:
- **web** (odoo:17.0): Main application server with custom addon mounting
- **db** (postgres:16): PostgreSQL database with health checks
- **redis** (redis:7-alpine): Session store and cache

**Key Volumes**:
- `./custom_addons:/mnt/extra-addons`: Custom module mounting
- `./config/odoo.conf:/etc/odoo/odoo.conf`: Configuration binding
- `postgres-data`, `odoo-web-data`, `redis-data`: Persistent volumes

**Ports**:
- 8069: Odoo web interface
- 5434: PostgreSQL
- 6380: Redis

## File Organization

```
soya_estate/
├── models/
│   ├── __init__.py
│   ├── property.py (7.75 KB)
│   ├── property_type.py (9.67 KB)
│   └── property_offer.py (13.84 KB)
├── views/
│   ├── property_views.xml
│   ├── property_type_views.xml
│   └── property_offer_views.xml
├── security/
│   ├── ir.model.access.csv
│   └── soya_estate_rules.xml
├── controllers/
│   ├── main.py
│   └── portal.py
├── static/src/css/
│   └── soya_estate.css (Web assets)
├── wizards/
│   ├── close_property.py
│   └── close_property_views.xml
├── tests/ (Ready for implementation)
├── __manifest__.py
└── __init__.py
```

## Testing
**Framework**: Odoo testing framework (based on unittest)  
**Test Location**: `custom_addons/soya_estate/tests/`  
**Status**: Tests directory initialized but currently empty - ready for implementation

**Run Tests**:
```bash
docker-compose exec web odoo -c /etc/odoo/odoo.conf --test-enable -d soya_odoo_db
```

## Key Files Reference
- **Manifest**: `custom_addons/soya_estate/__manifest__.py` - Module metadata and data loading configuration
- **Odoo Config**: `config/odoo.conf` - Database, Redis, worker configuration
- **Docker Compose**: `docker-compose.yml` - Multi-container service orchestration
- **Security Rules**: `security/ir.model.access.csv` - Role-based access control
- **Domain Rules**: `security/soya_estate_rules.xml` - Record-level security policies
