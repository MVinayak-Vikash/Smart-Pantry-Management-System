# Smart Pantry Management System — Phase 1

An automated IoT-ready pantry inventory and consumption tracking system built with **FastAPI**, **SQLAlchemy**, **SQLite**, and **Streamlit**.

Phase 1 provides real-time stock monitoring, refill detection, consumption calculations, daily intake analytics, and threshold alerting for 4 household staples: **Rice, Sugar, Salt, and Ghee**.

---

## Table of Contents
1. [Project Objective](#1-project-objective)
2. [Phase 1 Scope](#2-phase-1-scope)
3. [System Architecture](#3-system-architecture)
4. [Database Structure](#4-database-structure)
5. [API Endpoints](#5-api-endpoints)
6. [Installation Guide (Windows)](#6-installation-guide-windows)
7. [Starting the FastAPI Backend](#7-starting-the-fastapi-backend)
8. [Starting the Streamlit Dashboard](#8-starting-the-streamlit-dashboard)
9. [How Simulated Sensor Data Works](#9-how-simulated-sensor-data-works)
10. [Future ESP32 Hardware Integration](#10-future-esp32-hardware-integration)
11. [Future RFID Container Integration](#11-future-rfid-container-integration)
12. [Future Recipe Recommendation Module](#12-future-recipe-recommendation-module)
13. [Running Automated Tests](#13-running-automated-tests)

---

## 1. Project Objective

The overall vision of the Smart Pantry Management System is an end-to-end intelligent kitchen solution combining ESP32 microcontrollers, load cells, RFID container identification, cloud data synchronization, nutritional intake monitoring, and smart recipe suggestions.

In **Phase 1**, the objective is to build the core data foundation, calculation engine, REST API, and visualization dashboard using simulated sensor readings to validate all business logic before hardware integration.

---

## 2. Phase 1 Scope

### Included in Phase 1:
* SQLite database storing initial, minimum, and current quantities for **Rice, Sugar, Salt, and Ghee**.
* Chronological logging of weight readings in a dedicated `weight_readings` table.
* Consumption calculation that accurately distinguishes **consumption (weight loss)** from **refills/replenishments (weight increase)** without misattributing refills to consumption.
* Calculation of **Average Daily Intake** ($\frac{\text{total consumption}}{\text{days with consumption data}}$).
* Three-tier **Stock Availability Logic**:
  * `AVAILABLE`: $\text{current\_quantity} > \text{minimum\_quantity}$
  * `LOW`: $0 < \text{current\_quantity} \le \text{minimum\_quantity}$
  * `UNAVAILABLE`: $\text{current\_quantity} \le 0$
* Two-tier **Intake Alert Logic**:
  * `NORMAL`: $\text{average\_daily\_intake} \le \text{high\_intake\_threshold}$
  * `HIGH`: $\text{average\_daily\_intake} > \text{high\_intake\_threshold}$
  * `INSUFFICIENT DATA`: Insufficient historical records to determine intake pattern.
* **Estimated Remaining Days** calculation: $\frac{\text{current\_quantity}}{\text{average\_daily\_intake}}$.
* Streamlit interactive web dashboard displaying cards, visual color-coded badges, historical trends, and sensor simulation tools.
* 100% automated test suite covering all 12 criteria with `pytest`.

### Excluded from Phase 1 (Deferred to Future Phases):
* ESP32 firmware & physical HX711 / load cell wiring.
* Physical RFID reader / tag scanning.
* Recipe recommendation engine & machine learning models.
* Camera / image classification.

---

## 3. System Architecture

```
smart-pantry/
├── backend/
│   ├── __init__.py          # Package initialization
│   ├── database.py          # SQLite engine, SessionLocal, modular DB URL
│   ├── models.py            # SQLAlchemy Item and WeightReading models
│   ├── schemas.py           # Pydantic request/response validation schemas
│   ├── calculations.py      # Pure mathematical & business logic functions
│   ├── crud.py              # Database queries, updates, and seed functions
│   └── main.py              # FastAPI application, CORS, lifespan, REST routes
├── dashboard/
│   └── app.py               # Streamlit interactive UI, cards, charts, simulator
├── data/
│   └── pantry.db            # SQLite database file (auto-generated)
├── tests/
│   ├── __init__.py
│   ├── test_calculations.py # Unit tests for pure calculation functions
│   └── test_api.py          # Functional/integration tests for FastAPI endpoints
├── requirements.txt         # Python project dependencies
└── README.md                # System documentation and execution guide
```

The architecture is strictly modular:
* **Separation of Concerns**: Database models (`models.py`) are decoupled from API schemas (`schemas.py`).
* **Isolated Pure Logic**: All consumption, intake, and status calculations are encapsulated in `calculations.py`, enabling 100% unit test coverage independent of database or HTTP layers.
* **Database Agility**: `database.py` defaults to SQLite in `data/pantry.db`, but can be pointed to PostgreSQL or Supabase simply by providing a `DATABASE_URL` environment variable.

---

## 4. Database Structure

### `items` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique item ID |
| `name` | String | Unique, Indexed, Not Null | Staple name (Rice, Sugar, Salt, Ghee) |
| `unit` | String | Not Null, Default: `'g'` | Measurement unit (grams) |
| `initial_quantity` | Float | Not Null | Starting capacity (g) |
| `current_quantity` | Float | Not Null | Current live weight (g) |
| `minimum_quantity` | Float | Not Null | Low-stock warning trigger (g) |
| `high_intake_threshold` | Float | Not Null | Configurable high-intake alert limit (g/day) |
| `rfid_uid` | String | Nullable, Unique | Reserved for future RFID container tagging |
| `created_at` | DateTime | Not Null | Creation timestamp (UTC) |
| `updated_at` | DateTime | Not Null | Last update timestamp (UTC) |

#### Initial Item Configuration:
| Item | Initial Quantity | Minimum Quantity | Configurable High-Intake Threshold* |
| :--- | :---: | :---: | :---: |
| **Rice** | 5,000 g (5.0 kg) | 1,000 g (1.0 kg) | 300 g / day |
| **Sugar** | 2,000 g (2.0 kg) | 500 g (0.5 kg) | 50 g / day |
| **Salt** | 1,000 g (1.0 kg) | 250 g (0.25 kg) | 5 g / day |
| **Ghee** | 1,000 g (1.0 kg) | 250 g (0.25 kg) | 30 g / day |

*\*Note: High-intake thresholds are software demonstration thresholds for dietary awareness and can be adjusted per household preferences.*

### `weight_readings` Table
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | Integer | Primary Key, Auto-increment | Unique reading ID |
| `item_id` | Integer | Foreign Key (`items.id`), Indexed | Linked pantry item |
| `weight` | Float | Not Null | Recorded weight in grams |
| `timestamp` | DateTime | Indexed, Not Null | Telemetry timestamp (UTC) |

---

## 5. API Endpoints

Interactive Swagger API documentation is available at `http://127.0.0.1:8000/docs`.

### 1. Health Check
* **`GET /health`**
  * Verifies server status.

### 2. Get All Pantry Items
* **`GET /items`**
  * Returns overview of all 4 items: name, current quantity, unit, availability status, average daily intake, intake status, and estimated remaining days.

### 3. Get Specific Item Details
* **`GET /items/{item_id}`**
  * Returns detailed profile for an item, including thresholds, status, and recent historical weight readings.

### 4. Record a Weight Reading (Telemetry Endpoint)
* **`POST /items/{item_id}/weight`**
  * Ingests a new weight measurement (from simulator or future ESP32).
  * Validates $weight \ge 0$.
  * Updates item current quantity and returns new calculated statuses.
  * **Payload Example**:
    ```json
    {
      "weight": 3200.0
    }
    ```

### 5. Get Consumption History
* **`GET /items/{item_id}/consumption`**
  * Returns chronological consumption and refill intervals:
    * Previous weight
    * Current weight
    * Consumed amount
    * Refill amount
    * Aggregated metrics: total consumption, total refill, days tracked, and average daily intake.

### 6. Get Dashboard Summary
* **`GET /dashboard`**
  * Returns aggregated metrics for the dashboard: item cards list, total items, available count, low stock count, unavailable count, and high intake count.

### 7. Seed Simulated Sample Data
* **`POST /seed`**
  * Populates multi-day realistic historical readings across all 4 items for live presentation and testing.

---

## 6. Installation Guide (Windows)

### Prerequisites:
* Python 3.11 or 3.12 installed on your Windows machine.
* PowerShell or Windows Command Prompt.

### Step 1: Open PowerShell in the Project Directory
```powershell
cd "e:\Smart Pantry Management System"
```

### Step 2: Create and Activate Virtual Environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
*(If script execution is restricted in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

---

## 7. Starting the FastAPI Backend

Run the Uvicorn server from the project root:

```powershell
uvicorn backend.main:app --reload --port 8000
```

* API will be live at: `http://127.0.0.1:8000`
* Interactive API Documentation (Swagger UI): `http://127.0.0.1:8000/docs`
* SQLite database file `data/pantry.db` will be initialized automatically on startup.

---

## 8. Starting the Streamlit Dashboard

In a separate terminal window (with `.venv` activated):

```powershell
streamlit run dashboard/app.py
```

* Dashboard UI will open automatically in your browser at: `http://localhost:8501`
* Features:
  * **Overview Cards**: Rice, Sugar, Salt, Ghee with real-time stock, intake rates, and color badges.
  * **Visual Badges**:
    * `AVAILABLE` (Green)
    * `LOW STOCK` (Yellow / Orange)
    * `UNAVAILABLE` (Red)
    * `NORMAL` (Neutral / Green)
    * `HIGH INTAKE` (Orange Warning)
    * `INSUFFICIENT DATA` (Grey)
  * **Historical Weight Decay Trends**: Interactive charts showing weight changes.
  * **Consumption Logs Table**: Distinguishing usage drops from replenishment refills.
  * **Simulated Sensor Controls**: One-click sample dataset generation and custom weight reading submission.

---

## 9. How Simulated Sensor Data Works

To allow full demonstration without hardware:
1. **Sample Historical Seed**:
   * Rice: $5000 \to 4750 \to 4500 \to 4250 \to 4000 \to 3750$ g (Average: 250 g/day $\to$ NORMAL)
   * Sugar: $2000 \to 1950 \to 1900 \to 1850 \to 1800$ g (Average: 50 g/day $\to$ NORMAL)
   * Salt: $1000 \to 990 \to 980 \to 970 \to 960$ g (Average: 10 g/day $> 5$ g/day threshold $\to$ HIGH WARNING)
   * Ghee: $1000 \to 970 \to 940 \to 910 \to 880$ g (Average: 30 g/day $\to$ NORMAL)
   * Clicking **"Load Sample Historical Data"** in the Streamlit sidebar or sending `POST /seed` injects these records timestamped 1 day apart.
2. **Interactive Telemetry Simulation**:
   * Users can select any item from the sidebar, type any simulated weight in grams, and click **"Send Weight Reading"**.
   * The backend processes the reading immediately and updates inventory and intake statuses in real time.

---

## 10. Future ESP32 Hardware Integration

Phase 1 is explicitly designed to accept hardware telemetry in subsequent phases:

```
[ Pantry Container ]
         │
         ▼
[ Load Cell (Strain Gauge) ]
         │
         ▼
[ HX711 24-Bit ADC Module ]
         │
         ▼
[ ESP32 Microcontroller ]
         │ (Wi-Fi / HTTP POST)
         ▼
[ FastAPI Endpoint: POST /items/{item_id}/weight ]
         │
         ▼
[ SQLite / Cloud Database ]
```

When hardware is deployed:
1. The ESP32 reads calibration data from the HX711 module.
2. An HTTP `POST` request is sent via Wi-Fi with JSON `{"weight": calibrated_grams}` to `http://<server-ip>:8000/items/<item_id>/weight`.
3. No backend schema modifications are required—the endpoint is already fully functional.

---

## 11. Future RFID Container Integration

To support dynamic container positioning:
* The `items` table includes a dedicated `rfid_uid` column (`VARCHAR`, indexed, nullable).
* In Phase 2:
  1. An RC522 RFID reader connected to the ESP32 platform detects a passive RFID sticker on the container base.
  2. The RFID UID maps the container to the corresponding pantry item record.
  3. Load-cell weight is associated with the scanned `item_id`.

---

## 12. Future Recipe Recommendation Module

Phase 1 lays the foundation for intelligent kitchen assistants:
* Inventory and available quantities are exposed via `GET /items`.
* In Phase 3:
  1. A recommendation service queries `GET /items` to obtain currently `AVAILABLE` ingredients.
  2. Recipes requiring missing or `LOW`/`UNAVAILABLE` items are filtered out or flagged for shopping.
  3. High-intake items (e.g. excessive salt or sugar) can trigger suggestions for low-sodium or sugar-free alternatives.

---

## 13. Running Automated Tests

Run the complete test suite using `pytest`:

```powershell
.venv\Scripts\pytest -v
```

All 19 tests across `test_calculations.py` and `test_api.py` validate:
* Item initialization and retrieval
* Negative weight rejection (422) and invalid ID (404)
* Decrease vs. refill differentiation
* Daily intake averaging across multi-day records
* Status transitions: `AVAILABLE` $\leftrightarrow$ `LOW` $\leftrightarrow$ `UNAVAILABLE`
* Threshold warnings: `NORMAL` $\leftrightarrow$ `HIGH` $\leftrightarrow$ `INSUFFICIENT DATA`
* Remaining days estimation logic
