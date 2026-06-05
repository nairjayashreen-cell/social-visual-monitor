# AI Visual Threat Monitoring

## Current Version

MVP v2.0 – Multi-Scale Logo Detection & Threat Monitoring

### Overview

AI Visual Threat Monitoring is a brand protection platform that scans social media content, detects brand logos, identifies potential misuse, and generates risk-based reports for investigation.

### Supported Brands

* ICICI
* Groww
* Motilal Oswal
* Tata Capital
* Zerodha
* Upstox
* SBI
* Anand Rathi

### Supported Platforms

* Instagram ✅
* Facebook (Planned)
* LinkedIn (Planned)

### Core Features

#### Brand Monitoring

* Multi-brand monitoring
* Instagram post scanning
* Post URL tracking
* IST timestamp conversion
* Historical scan storage

#### Logo Detection Engine

* Multi-scale template matching
* Logo region detection
* Small watermark detection
* SSIM similarity scoring
* ImageHash similarity scoring
* Hybrid confidence scoring
* Risk classification (High / Medium / Low)

#### Analytics & Intelligence

* Scan history dashboard
* Risk distribution analytics
* Average score tracking
* Repeat offender tracking
* Historical scan comparisons

#### Reporting

* Advanced Excel export
* Executive summary sheet
* High-risk detections report
* Risk distribution charts
* Detection-level reporting

#### Infrastructure

* FastAPI backend
* SQLite persistence
* Apify integration
* Apify proxy image retrieval
* Render deployment
* Logo persistence management

### Risk Levels

* High Risk: 65%+
* Medium Risk: 35–64%
* Low Risk: Below 35%

### Roadmap

#### MVP v2.1

* AI-powered threat classification
* Scam detection
* Impersonation detection
* Fake recruitment detection

#### MVP v2.2

* Automated monitoring
* Scheduled scans
* Email alerts
* WhatsApp notifications

#### MVP v2.3

* Facebook monitoring
* LinkedIn monitoring
* Cross-platform intelligence dashboard

### Tech Stack

* FastAPI
* OpenCV
* Scikit-Image (SSIM)
* ImageHash
* OpenPyXL
* SQLite
* Pandas
* Apify
* Render
