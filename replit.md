Real Estate Management System
Overview
This is a comprehensive real estate management system built with Flask that supports Arabic language and RTL layout. The system manages property sales and rental offers across different districts (Central and South), employee management with role-based permissions, client orders, and system activity logging. It provides a complete workflow for real estate agencies to track properties, manage staff, and handle client interactions.

User Preferences
Preferred communication style: Simple, everyday language.

System Architecture
Frontend Architecture
Template Engine: Jinja2 templates with Flask
UI Framework: Bootstrap with custom dark theme and RTL support for Arabic
Styling: Custom CSS with responsive design and Font Awesome icons
Layout: Base template with modular components for different sections
Language Support: Arabic language with right-to-left (RTL) text direction
Backend Architecture
Web Framework: Flask with Blueprint-style organization
Authentication: Flask-Login with session-based user management
Security: Werkzeug password hashing and secure file handling
Authorization: Role-based permission system with decorators
File Handling: Secure file upload with allowed extensions validation
Data Storage Solutions
Database: SQLite with SQLAlchemy ORM
Models:
Employee model with UserMixin for authentication
Rental offers separated by district (Central/South)
Sale offers separated by district (Central/South)
Customer orders with detailed property requirements
Activity logs for audit trail
File Storage: Local filesystem for property images in uploads directory
Permission System
Granular Permissions: Separate permissions for each operation (view, add, edit, delete)
District-based Access: Different permissions for Central and South district operations
Employee Management: Hierarchical access control for staff management
Activity Logging: Comprehensive logging of user actions for audit purposes
Core Features
Multi-district Support: Separate management for Central and South property districts
Property Management: Dual system for rental and sale offers with distinct workflows
Employee Management: Full CRUD operations with role-based access control
Order Management: Client requirement tracking with detailed property specifications
Dashboard Analytics: Real-time statistics and counts for different data types
Activity Monitoring: Complete audit trail of system usage and changes
External Dependencies
Python Packages
Flask: Core web framework for application structure
Flask-SQLAlchemy: Database ORM for data persistence
Flask-Login: User session and authentication management
Werkzeug: Security utilities for password hashing and file handling
Frontend Libraries
Bootstrap: UI framework with dark theme variant
Font Awesome: Icon library for consistent visual elements
Custom CSS: Additional styling for RTL support and responsive design
Database
SQLite: Lightweight database for development and small-scale deployment
Note: System architecture supports easy migration to PostgreSQL for production use
File System
Local Storage: Image uploads stored in local uploads directory
Allowed Formats: PNG, JPG, JPEG, GIF image formats supported
Security: Filename sanitization and extension validation