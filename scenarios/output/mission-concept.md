# Pyra · Wildfire CubeSat — Mission concept report

Baseline: 5aecbae3-cc26-4dff-8fd5-4df0c5512041 · Model revision: 11
Generated: 2026-09-09T16:30:30.706477+00:00

## Scope
Design a 12U CubeSat mission that detects and monitors wildfires over southern Europe. Deliver useful imagery within 30 minutes of acquisition, operate for at least two years, use a rideshare launch, and remain within a €12 million programme budget.

**Conceptual study only. Latency, coverage, detection performance, lifetime and programme cost remain unverified.**

## Selected concept
selective

## Objective

### objective: Detect and monitor wildfires over southern Europe
Explicit assumption · accepted · Owner: science
```json
{
  "stakeholder": "Civil protection and wildfire monitoring teams",
  "priority": "must",
  "measure_of_success": "Useful thermal anomalies and contextual imagery"
}
```
Traceability: depends_on → scope

## Requirement

### req-observe: The mission shall acquire wildfire monitoring imagery over southern Europe.
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Derived from the mission owner brief and approved scope",
  "source": "Mission brief / scope assumption",
  "level": "stakeholder",
  "priority": "must",
  "verification_method": "demonstration"
}
```
Traceability: derives_from → objective

### req-latency: The ground segment shall deliver useful imagery within 30 minutes of acquisition.
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Derived from the mission owner brief and approved scope",
  "source": "Mission brief / scope assumption",
  "level": "system",
  "priority": "must",
  "verification_method": "analysis"
}
```
Traceability: derives_from → objective

### req-life: The spacecraft shall support operations for at least two years.
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Derived from the mission owner brief and approved scope",
  "source": "Mission brief / scope assumption",
  "level": "system",
  "priority": "must",
  "verification_method": "analysis"
}
```
Traceability: derives_from → objective

### req-launch: The spacecraft shall fit a 12U rideshare deployer envelope.
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Derived from the mission owner brief and approved scope",
  "source": "Mission brief / scope assumption",
  "level": "system",
  "priority": "must",
  "verification_method": "inspection"
}
```
Traceability: derives_from → objective

### req-cost: The programme shall remain within €12 million.
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Derived from the mission owner brief and approved scope",
  "source": "Mission brief / scope assumption",
  "level": "stakeholder",
  "priority": "must",
  "verification_method": "review"
}
```
Traceability: derives_from → objective

## ArchitectureAlternative

### wide: A · Wide-area continuous imaging
Explicit assumption · accepted · Owner: systems
```json
{
  "benefits": [
    "More contextual imagery"
  ],
  "disadvantages": [
    "Data volume exceeds S-band downlink"
  ],
  "risks": [
    "Contact assumptions",
    "Payload sensitivity unverified"
  ],
  "conops": "Acquire thermal strips and store complete imagery; daily S-band ground delivery.",
  "payload": "Thermal imager with contextual channel; 5% observation duty cycle",
  "ground": "Single-network S-band contacts",
  "cost_estimate_eur": 10500000,
  "cost_basis": "Explicit programme estimate, not a quotation"
}
```
Traceability: depends_on → req-observe, depends_on → resources

### selective: B · Event-selective imaging + X-band
Explicit assumption · accepted · Owner: systems
```json
{
  "benefits": [
    "Lower data demand",
    "Higher downlink capacity"
  ],
  "disadvantages": [
    "Onboard filtering can miss weak anomalies",
    "Larger ground antenna dependency"
  ],
  "risks": [
    "False negatives",
    "Unverified latency and revisit"
  ],
  "conops": "Observe targeted strips, filter events onboard, retain context, downlink via X-band; S-band for TT&C.",
  "payload": "Thermal imager with event filtering; 2% observation duty cycle",
  "ground": "Scheduled X-band network",
  "cost_estimate_eur": 11500000,
  "cost_basis": "Explicit programme estimate, not a quotation"
}
```
Traceability: depends_on → req-observe, depends_on → resources

## Function

### detect: Detect, locate and prioritize thermal anomalies
Explicit assumption · accepted · Owner: systems
```json
{
  "inputs": [
    "Thermal radiance"
  ],
  "outputs": [
    "Geolocated events"
  ],
  "performance": "Sensitivity unknown",
  "allocated_element": "imager"
}
```
Traceability: depends_on → req-observe

### deliver: Store and deliver imagery to mission users
Explicit assumption · accepted · Owner: systems
```json
{
  "inputs": [
    "Image products"
  ],
  "outputs": [
    "Ground products"
  ],
  "performance": "30 minutes required; unverified",
  "allocated_element": "bus-component"
}
```
Traceability: depends_on → req-latency

## Component

### imager: Thermal payload
Explicit assumption · accepted · Owner: systems
```json
{
  "type": "payload",
  "parent": "spacecraft",
  "pointing": "Ground-target tracking; accuracy TBD",
  "calibration": "Onboard reference and vicarious calibration; validation pending",
  "maturity": "concept"
}
```
Traceability: depends_on → detect

### bus-component: 12U platform and ground service
Explicit assumption · accepted · Owner: systems
```json
{
  "type": "platform",
  "parent": "spacecraft",
  "aocs": "Three-axis stabilized; pointing budget TBD",
  "thermal": "Passive concept; thermal balance unverified",
  "obc": "Event filtering and solid-state storage",
  "maturity": "concept"
}
```
Traceability: depends_on → deliver

## Interface

### interface: Payload → onboard data handling
Explicit assumption · accepted · Owner: systems
```json
{
  "endpoints": [
    "imager",
    "bus-component"
  ],
  "exchanges": [
    "Image packets",
    "Time tags"
  ],
  "direction": "payload to bus",
  "medium": "SpaceWire assumed",
  "constraints": [
    "Peak input rate 20 Mbit/s; verify hardware compatibility"
  ]
}
```
Traceability: depends_on → imager, depends_on → bus-component

## Budget

### wide-mass: wide · mass
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "wide",
  "entries": [
    {
      "name": "Payload",
      "cbe": {
        "value": 3,
        "unit": "kg"
      },
      "allocated": {
        "value": 3.6,
        "unit": "kg"
      }
    },
    {
      "name": "Structure",
      "cbe": {
        "value": 2,
        "unit": "kg"
      },
      "allocated": {
        "value": 2.4,
        "unit": "kg"
      }
    },
    {
      "name": "Power",
      "cbe": {
        "value": 2.5,
        "unit": "kg"
      },
      "allocated": {
        "value": 3.0,
        "unit": "kg"
      }
    },
    {
      "name": "Avionics/AOCS",
      "cbe": {
        "value": 2,
        "unit": "kg"
      },
      "allocated": {
        "value": 2.4,
        "unit": "kg"
      }
    },
    {
      "name": "Communications",
      "cbe": {
        "value": 1,
        "unit": "kg"
      },
      "allocated": {
        "value": 1.2,
        "unit": "kg"
      }
    }
  ],
  "total": {
    "value": 12.6,
    "unit": "kg"
  },
  "limit": {
    "value": 20,
    "unit": "kg"
  },
  "margin": {
    "value": 7.4,
    "unit": "kg"
  },
  "compliant": true
}
```
Traceability: depends_on → wide-mass-analysis

### wide-power: wide · power
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "wide",
  "average_load": {
    "value": 14.0,
    "unit": "W"
  },
  "generated": {
    "value": 44.964013,
    "unit": "Wh"
  },
  "consumed": {
    "value": 22.283828,
    "unit": "Wh"
  },
  "margin": {
    "value": 22.680186,
    "unit": "Wh"
  },
  "eclipse_energy": {
    "value": 8.295023,
    "unit": "Wh"
  },
  "usable_battery": {
    "value": 24.0,
    "unit": "Wh"
  },
  "battery_margin": {
    "value": 15.704977,
    "unit": "Wh"
  },
  "compliant": true
}
```
Traceability: depends_on → wide-power-analysis

### wide-data: wide · data
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "wide",
  "daily": {
    "value": 43200000000.0,
    "unit": "bit"
  },
  "storage": {
    "value": 256000000000.0,
    "unit": "bit"
  },
  "margin": {
    "value": 212800000000.0,
    "unit": "bit"
  },
  "compliant": true
}
```
Traceability: depends_on → wide-data-analysis

### wide-link: wide · link
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "wide",
  "fspl_db": {
    "value": 162.818062,
    "unit": "dimensionless"
  },
  "ebn0_db": {
    "value": 17.999593,
    "unit": "dimensionless"
  },
  "link_margin_db": {
    "value": 12.999593,
    "unit": "dimensionless"
  },
  "capacity": {
    "value": 1680000000.0,
    "unit": "bit"
  },
  "margin": {
    "value": -41520000000.0,
    "unit": "bit"
  },
  "compliant": false
}
```
Traceability: depends_on → wide-link-analysis

### selective-mass: selective · mass
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "selective",
  "entries": [
    {
      "name": "Payload",
      "cbe": {
        "value": 3,
        "unit": "kg"
      },
      "allocated": {
        "value": 3.6,
        "unit": "kg"
      }
    },
    {
      "name": "Structure",
      "cbe": {
        "value": 2,
        "unit": "kg"
      },
      "allocated": {
        "value": 2.4,
        "unit": "kg"
      }
    },
    {
      "name": "Power",
      "cbe": {
        "value": 2.5,
        "unit": "kg"
      },
      "allocated": {
        "value": 3.0,
        "unit": "kg"
      }
    },
    {
      "name": "Avionics/AOCS",
      "cbe": {
        "value": 2,
        "unit": "kg"
      },
      "allocated": {
        "value": 2.4,
        "unit": "kg"
      }
    },
    {
      "name": "Communications",
      "cbe": {
        "value": 1.5,
        "unit": "kg"
      },
      "allocated": {
        "value": 1.8,
        "unit": "kg"
      }
    }
  ],
  "total": {
    "value": 13.2,
    "unit": "kg"
  },
  "limit": {
    "value": 20,
    "unit": "kg"
  },
  "margin": {
    "value": 6.8,
    "unit": "kg"
  },
  "compliant": true
}
```
Traceability: depends_on → selective-mass-analysis

### selective-power: selective · power
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "selective",
  "average_load": {
    "value": 14.0,
    "unit": "W"
  },
  "generated": {
    "value": 44.964013,
    "unit": "Wh"
  },
  "consumed": {
    "value": 22.283828,
    "unit": "Wh"
  },
  "margin": {
    "value": 22.680186,
    "unit": "Wh"
  },
  "eclipse_energy": {
    "value": 8.295023,
    "unit": "Wh"
  },
  "usable_battery": {
    "value": 24.0,
    "unit": "Wh"
  },
  "battery_margin": {
    "value": 15.704977,
    "unit": "Wh"
  },
  "compliant": true
}
```
Traceability: depends_on → selective-power-analysis

### selective-data: selective · data
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "selective",
  "daily": {
    "value": 8640000000.0,
    "unit": "bit"
  },
  "storage": {
    "value": 256000000000.0,
    "unit": "bit"
  },
  "margin": {
    "value": 247360000000.0,
    "unit": "bit"
  },
  "compliant": true
}
```
Traceability: depends_on → selective-data-analysis

### selective-link: selective · link
Deterministic calculation · accepted · Owner: tool
```json
{
  "candidate": "selective",
  "fspl_db": {
    "value": 174.245885,
    "unit": "dimensionless"
  },
  "ebn0_db": {
    "value": 13.571769,
    "unit": "dimensionless"
  },
  "link_margin_db": {
    "value": 8.571769,
    "unit": "dimensionless"
  },
  "capacity": {
    "value": 16799999999.999998,
    "unit": "bit"
  },
  "margin": {
    "value": 8159999999.999998,
    "unit": "bit"
  },
  "compliant": true
}
```
Traceability: depends_on → selective-link-analysis

## Claim

### mission-orbit-claim: mission: preliminary orbit results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "period": {
      "value": 5730.127089,
      "unit": "second"
    },
    "eclipse": {
      "value": 2133.006041,
      "unit": "second"
    },
    "coverage": "Unknown: no access propagation",
    "latency": "Unknown: daily capacity is not latency"
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → mission-orbit-analysis

### wide-mass-claim: wide: preliminary mass results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "entries": [
      {
        "name": "Payload",
        "cbe": {
          "value": 3,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.6,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "cbe": {
          "value": 2.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.0,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "cbe": {
          "value": 1,
          "unit": "kg"
        },
        "allocated": {
          "value": 1.2,
          "unit": "kg"
        }
      }
    ],
    "total": {
      "value": 12.6,
      "unit": "kg"
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    },
    "margin": {
      "value": 7.4,
      "unit": "kg"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → wide-mass-analysis

### wide-power-claim: wide: preliminary power results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "average_load": {
      "value": 14.0,
      "unit": "W"
    },
    "generated": {
      "value": 44.964013,
      "unit": "Wh"
    },
    "consumed": {
      "value": 22.283828,
      "unit": "Wh"
    },
    "margin": {
      "value": 22.680186,
      "unit": "Wh"
    },
    "eclipse_energy": {
      "value": 8.295023,
      "unit": "Wh"
    },
    "usable_battery": {
      "value": 24.0,
      "unit": "Wh"
    },
    "battery_margin": {
      "value": 15.704977,
      "unit": "Wh"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → wide-power-analysis

### wide-data-claim: wide: preliminary data results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "daily": {
      "value": 43200000000.0,
      "unit": "bit"
    },
    "storage": {
      "value": 256000000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": 212800000000.0,
      "unit": "bit"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → wide-data-analysis

### wide-link-claim: wide: preliminary link results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "fspl_db": {
      "value": 162.818062,
      "unit": "dimensionless"
    },
    "ebn0_db": {
      "value": 17.999593,
      "unit": "dimensionless"
    },
    "link_margin_db": {
      "value": 12.999593,
      "unit": "dimensionless"
    },
    "capacity": {
      "value": 1680000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": -41520000000.0,
      "unit": "bit"
    },
    "compliant": false
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → wide-link-analysis

### selective-mass-claim: selective: preliminary mass results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "entries": [
      {
        "name": "Payload",
        "cbe": {
          "value": 3,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.6,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "cbe": {
          "value": 2.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.0,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "cbe": {
          "value": 1.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 1.8,
          "unit": "kg"
        }
      }
    ],
    "total": {
      "value": 13.2,
      "unit": "kg"
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    },
    "margin": {
      "value": 6.8,
      "unit": "kg"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → selective-mass-analysis

### selective-power-claim: selective: preliminary power results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "average_load": {
      "value": 14.0,
      "unit": "W"
    },
    "generated": {
      "value": 44.964013,
      "unit": "Wh"
    },
    "consumed": {
      "value": 22.283828,
      "unit": "Wh"
    },
    "margin": {
      "value": 22.680186,
      "unit": "Wh"
    },
    "eclipse_energy": {
      "value": 8.295023,
      "unit": "Wh"
    },
    "usable_battery": {
      "value": 24.0,
      "unit": "Wh"
    },
    "battery_margin": {
      "value": 15.704977,
      "unit": "Wh"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → selective-power-analysis

### selective-data-claim: selective: preliminary data results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "daily": {
      "value": 8640000000.0,
      "unit": "bit"
    },
    "storage": {
      "value": 256000000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": 247360000000.0,
      "unit": "bit"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → selective-data-analysis

### selective-link-claim: selective: preliminary link results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "fspl_db": {
      "value": 174.245885,
      "unit": "dimensionless"
    },
    "ebn0_db": {
      "value": 13.571769,
      "unit": "dimensionless"
    },
    "link_margin_db": {
      "value": 8.571769,
      "unit": "dimensionless"
    },
    "capacity": {
      "value": 16799999999.999998,
      "unit": "bit"
    },
    "margin": {
      "value": 8159999999.999998,
      "unit": "bit"
    },
    "compliant": true
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → selective-link-analysis

### concept-trade-claim: concept: preliminary trade results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "scores": {
      "wide": 2.55,
      "selective": 3.9
    },
    "recommendation": "selective"
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → concept-trade-analysis

### selection-trade-claim: selection: preliminary trade results
Deterministic calculation · accepted · Owner: tool
```json
{
  "outputs": {
    "scores": {
      "wide": 2.55,
      "selective": 3.9
    },
    "recommendation": "selective"
  },
  "validity": "Conditional on recorded assumptions"
}
```
Traceability: depends_on → selection-trade-analysis

## Evidence

## Parameter

## AnalysisRun

### mission-orbit-analysis: mission · orbit calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "orbit",
  "version": "1.0",
  "inputs": {
    "altitude": {
      "value": 550,
      "unit": "km"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.974067+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "period": {
      "value": 5730.127089,
      "unit": "second"
    },
    "eclipse": {
      "value": 2133.006041,
      "unit": "second"
    },
    "coverage": "Unknown: no access propagation",
    "latency": "Unknown: daily capacity is not latency"
  },
  "status": "valid",
  "elapsed_seconds": 0.0006358099999488331
}
```
Traceability: depends_on → orbit-assumption

### wide-mass-analysis: wide · mass calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "mass",
  "version": "1.0",
  "inputs": {
    "entries": [
      {
        "name": "Payload",
        "mass": {
          "value": 3,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "mass": {
          "value": 2,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "mass": {
          "value": 2.5,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "mass": {
          "value": 2,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "mass": {
          "value": 1,
          "unit": "kg"
        }
      }
    ],
    "margin": {
      "value": 0.2,
      "unit": ""
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.974811+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "entries": [
      {
        "name": "Payload",
        "cbe": {
          "value": 3,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.6,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "cbe": {
          "value": 2.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.0,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "cbe": {
          "value": 1,
          "unit": "kg"
        },
        "allocated": {
          "value": 1.2,
          "unit": "kg"
        }
      }
    ],
    "total": {
      "value": 12.6,
      "unit": "kg"
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    },
    "margin": {
      "value": 7.4,
      "unit": "kg"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0030751509998481197
}
```
Traceability: depends_on → wide, depends_on → resources, depends_on → operations

### wide-power-analysis: wide · power calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "power",
  "version": "1.0",
  "inputs": {
    "modes": [
      {
        "name": "observe",
        "fraction": {
          "value": 0.2,
          "unit": ""
        },
        "loads": {
          "payload": {
            "value": 20,
            "unit": "W"
          },
          "bus": {
            "value": 10,
            "unit": "W"
          }
        }
      },
      {
        "name": "standby",
        "fraction": {
          "value": 0.8,
          "unit": ""
        },
        "loads": {
          "bus": {
            "value": 10,
            "unit": "W"
          }
        }
      }
    ],
    "period": {
      "value": 5730.127089,
      "unit": "second"
    },
    "eclipse": {
      "value": 2133.006041,
      "unit": "second"
    },
    "solar": {
      "value": 45,
      "unit": "W"
    },
    "battery": {
      "value": 40,
      "unit": "Wh"
    },
    "depth_of_discharge": {
      "value": 0.6,
      "unit": ""
    },
    "eclipse_load": {
      "value": 14,
      "unit": "W"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.978102+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "average_load": {
      "value": 14.0,
      "unit": "W"
    },
    "generated": {
      "value": 44.964013,
      "unit": "Wh"
    },
    "consumed": {
      "value": 22.283828,
      "unit": "Wh"
    },
    "margin": {
      "value": 22.680186,
      "unit": "Wh"
    },
    "eclipse_energy": {
      "value": 8.295023,
      "unit": "Wh"
    },
    "usable_battery": {
      "value": 24.0,
      "unit": "Wh"
    },
    "battery_margin": {
      "value": 15.704977,
      "unit": "Wh"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0007274409999808995
}
```
Traceability: depends_on → wide, depends_on → resources, depends_on → operations

### wide-data-analysis: wide · data calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "data",
  "version": "1.0",
  "inputs": {
    "rate": {
      "value": 20,
      "unit": "Mbit/s"
    },
    "duty": {
      "value": 0.05,
      "unit": ""
    },
    "compression": {
      "value": 2,
      "unit": ""
    },
    "storage": {
      "value": 32,
      "unit": "Gbyte"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.978926+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "daily": {
      "value": 43200000000.0,
      "unit": "bit"
    },
    "storage": {
      "value": 256000000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": 212800000000.0,
      "unit": "bit"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0007880190000832954
}
```
Traceability: depends_on → wide, depends_on → resources, depends_on → operations

### wide-link-analysis: wide · link calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "link",
  "version": "1.0",
  "inputs": {
    "frequency": {
      "value": 2.2,
      "unit": "GHz"
    },
    "range": {
      "value": 1500,
      "unit": "km"
    },
    "rate": {
      "value": 1,
      "unit": "Mbit/s"
    },
    "tx_power": {
      "value": 5,
      "unit": "W"
    },
    "tx_gain_db": {
      "value": 3,
      "unit": ""
    },
    "rx_gain_db": {
      "value": 30,
      "unit": ""
    },
    "loss_db": {
      "value": 3,
      "unit": ""
    },
    "required_ebn0_db": {
      "value": 5,
      "unit": ""
    },
    "noise_temperature": {
      "value": 300,
      "unit": "K"
    },
    "contact": {
      "value": 40,
      "unit": "minute"
    },
    "efficiency": {
      "value": 0.7,
      "unit": ""
    },
    "demand": {
      "value": 43200000000.0,
      "unit": "bit"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.979802+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "fspl_db": {
      "value": 162.818062,
      "unit": "dimensionless"
    },
    "ebn0_db": {
      "value": 17.999593,
      "unit": "dimensionless"
    },
    "link_margin_db": {
      "value": 12.999593,
      "unit": "dimensionless"
    },
    "capacity": {
      "value": 1680000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": -41520000000.0,
      "unit": "bit"
    },
    "compliant": false
  },
  "status": "valid",
  "elapsed_seconds": 0.0010371280000072147
}
```
Traceability: depends_on → wide, depends_on → wide-data, depends_on → operations

### selective-mass-analysis: selective · mass calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "mass",
  "version": "1.0",
  "inputs": {
    "entries": [
      {
        "name": "Payload",
        "mass": {
          "value": 3,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "mass": {
          "value": 2,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "mass": {
          "value": 2.5,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "mass": {
          "value": 2,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "mass": {
          "value": 1.5,
          "unit": "kg"
        }
      }
    ],
    "margin": {
      "value": 0.2,
      "unit": ""
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.982006+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "entries": [
      {
        "name": "Payload",
        "cbe": {
          "value": 3,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.6,
          "unit": "kg"
        }
      },
      {
        "name": "Structure",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Power",
        "cbe": {
          "value": 2.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 3.0,
          "unit": "kg"
        }
      },
      {
        "name": "Avionics/AOCS",
        "cbe": {
          "value": 2,
          "unit": "kg"
        },
        "allocated": {
          "value": 2.4,
          "unit": "kg"
        }
      },
      {
        "name": "Communications",
        "cbe": {
          "value": 1.5,
          "unit": "kg"
        },
        "allocated": {
          "value": 1.8,
          "unit": "kg"
        }
      }
    ],
    "total": {
      "value": 13.2,
      "unit": "kg"
    },
    "limit": {
      "value": 20,
      "unit": "kg"
    },
    "margin": {
      "value": 6.8,
      "unit": "kg"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0026564210002106847
}
```
Traceability: depends_on → selective, depends_on → resources, depends_on → operations

### selective-power-analysis: selective · power calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "power",
  "version": "1.0",
  "inputs": {
    "modes": [
      {
        "name": "observe",
        "fraction": {
          "value": 0.2,
          "unit": ""
        },
        "loads": {
          "payload": {
            "value": 20,
            "unit": "W"
          },
          "bus": {
            "value": 10,
            "unit": "W"
          }
        }
      },
      {
        "name": "standby",
        "fraction": {
          "value": 0.8,
          "unit": ""
        },
        "loads": {
          "bus": {
            "value": 10,
            "unit": "W"
          }
        }
      }
    ],
    "period": {
      "value": 5730.127089,
      "unit": "second"
    },
    "eclipse": {
      "value": 2133.006041,
      "unit": "second"
    },
    "solar": {
      "value": 45,
      "unit": "W"
    },
    "battery": {
      "value": 40,
      "unit": "Wh"
    },
    "depth_of_discharge": {
      "value": 0.6,
      "unit": ""
    },
    "eclipse_load": {
      "value": 14,
      "unit": "W"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.984872+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "average_load": {
      "value": 14.0,
      "unit": "W"
    },
    "generated": {
      "value": 44.964013,
      "unit": "Wh"
    },
    "consumed": {
      "value": 22.283828,
      "unit": "Wh"
    },
    "margin": {
      "value": 22.680186,
      "unit": "Wh"
    },
    "eclipse_energy": {
      "value": 8.295023,
      "unit": "Wh"
    },
    "usable_battery": {
      "value": 24.0,
      "unit": "Wh"
    },
    "battery_margin": {
      "value": 15.704977,
      "unit": "Wh"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0003842070000246167
}
```
Traceability: depends_on → selective, depends_on → resources, depends_on → operations

### selective-data-analysis: selective · data calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "data",
  "version": "1.0",
  "inputs": {
    "rate": {
      "value": 20,
      "unit": "Mbit/s"
    },
    "duty": {
      "value": 0.02,
      "unit": ""
    },
    "compression": {
      "value": 4,
      "unit": ""
    },
    "storage": {
      "value": 32,
      "unit": "Gbyte"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.985712+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "daily": {
      "value": 8640000000.0,
      "unit": "bit"
    },
    "storage": {
      "value": 256000000000.0,
      "unit": "bit"
    },
    "margin": {
      "value": 247360000000.0,
      "unit": "bit"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0003998379997938173
}
```
Traceability: depends_on → selective, depends_on → resources, depends_on → operations

### selective-link-analysis: selective · link calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "link",
  "version": "1.0",
  "inputs": {
    "frequency": {
      "value": 8.2,
      "unit": "GHz"
    },
    "range": {
      "value": 1500,
      "unit": "km"
    },
    "rate": {
      "value": 10,
      "unit": "Mbit/s"
    },
    "tx_power": {
      "value": 5,
      "unit": "W"
    },
    "tx_gain_db": {
      "value": 8,
      "unit": ""
    },
    "rx_gain_db": {
      "value": 42,
      "unit": ""
    },
    "loss_db": {
      "value": 3,
      "unit": ""
    },
    "required_ebn0_db": {
      "value": 5,
      "unit": ""
    },
    "noise_temperature": {
      "value": 300,
      "unit": "K"
    },
    "contact": {
      "value": 40,
      "unit": "minute"
    },
    "efficiency": {
      "value": 0.7,
      "unit": ""
    },
    "demand": {
      "value": 8640000000.0,
      "unit": "bit"
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.988004+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "fspl_db": {
      "value": 174.245885,
      "unit": "dimensionless"
    },
    "ebn0_db": {
      "value": 13.571769,
      "unit": "dimensionless"
    },
    "link_margin_db": {
      "value": 8.571769,
      "unit": "dimensionless"
    },
    "capacity": {
      "value": 16799999999.999998,
      "unit": "bit"
    },
    "margin": {
      "value": 8159999999.999998,
      "unit": "bit"
    },
    "compliant": true
  },
  "status": "valid",
  "elapsed_seconds": 0.0011080369999945106
}
```
Traceability: depends_on → selective, depends_on → selective-data, depends_on → operations

### concept-trade-analysis: concept · trade calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "trade",
  "version": "1.0",
  "inputs": {
    "weights": {
      "science": 0.35,
      "capacity": 0.45,
      "simplicity": 0.2
    },
    "scores": {
      "wide": {
        "science": 5,
        "capacity": 0,
        "simplicity": 4
      },
      "selective": {
        "science": 3,
        "capacity": 5,
        "simplicity": 3
      }
    }
  },
  "source_revision": 5,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:29.989446+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "scores": {
      "wide": 2.55,
      "selective": 3.9
    },
    "recommendation": "selective"
  },
  "status": "valid",
  "elapsed_seconds": 3.402899983484531e-05
}
```
Traceability: depends_on → wide-link, depends_on → selective-link

### selection-trade-analysis: selection · trade calculation
Deterministic calculation · accepted · Owner: tool
```json
{
  "tool": "trade",
  "version": "1.0",
  "inputs": {
    "weights": {
      "science": 0.35,
      "capacity": 0.45,
      "simplicity": 0.2
    },
    "scores": {
      "wide": {
        "science": 5,
        "capacity": 0,
        "simplicity": 4
      },
      "selective": {
        "science": 3,
        "capacity": 5,
        "simplicity": 3
      }
    }
  },
  "source_revision": 6,
  "assumptions": [
    "Concept estimates; approved resources and operations assumptions"
  ],
  "timestamp": "2026-09-09T16:30:30.031285+00:00",
  "warnings": [
    "Preliminary concept sizing; assumed inputs are not validated hardware performance."
  ],
  "errors": [],
  "outputs": {
    "scores": {
      "wide": 2.55,
      "selective": 3.9
    },
    "recommendation": "selective"
  },
  "status": "valid",
  "elapsed_seconds": 5.950600007054163e-05
}
```
Traceability: depends_on → wide-link, depends_on → selective-link

## Assumption

### scope: Reference scenario applies: 12U, southern Europe, 30 minutes, two years, rideshare, €12M
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Incomplete brief requires a declared sizing basis",
  "impact": "May invalidate payload, orbit or mission feasibility",
  "confidence": 0.4,
  "validation_plan": "Confirm these constraints against the supplied brief; custom missions need edited requirements."
}
```
Traceability: 

### observation: Thermal anomalies and contextual images; assumed 100 m sampling and 100 km swath
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Incomplete brief requires a declared sizing basis",
  "impact": "May invalidate payload, orbit or mission feasibility",
  "confidence": 0.4,
  "validation_plan": "Validate detection sensitivity, geolocation, cloud effects and user needs with a payload study."
}
```
Traceability: 

### orbit-assumption: Assume circular 550 km LEO; access windows and revisit remain unknown
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Incomplete brief requires a declared sizing basis",
  "impact": "May invalidate payload, orbit or mission feasibility",
  "confidence": 0.4,
  "validation_plan": "Propagate actual orbit and ground stations before a preliminary design review."
}
```
Traceability: 

### operations: Assume 40 minutes of usable ground contact daily; this does not prove 30-minute delivery
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Incomplete brief requires a declared sizing basis",
  "impact": "May invalidate payload, orbit or mission feasibility",
  "confidence": 0.4,
  "validation_plan": "Simulate worst-case acquisition-to-user latency with actual station access and processing."
}
```
Traceability: 

### resources: Resource inputs are concept estimates with 20% mass contingency and 60% battery depth of discharge
Explicit assumption · accepted · Owner: science
```json
{
  "rationale": "Incomplete brief requires a declared sizing basis",
  "impact": "May invalidate payload, orbit or mission feasibility",
  "confidence": 0.4,
  "validation_plan": "Replace with qualified supplier and environmental evidence."
}
```
Traceability: 

## TradeStudy

### trade: Resolve the payload–ground capacity conflict
Explicit assumption · accepted · Owner: systems
```json
{
  "criteria": [
    "science",
    "capacity",
    "simplicity"
  ],
  "weights": {
    "science": 0.35,
    "capacity": 0.45,
    "simplicity": 0.2
  },
  "scores": {
    "wide": {
      "science": 5,
      "capacity": 0,
      "simplicity": 4
    },
    "selective": {
      "science": 3,
      "capacity": 5,
      "simplicity": 3
    }
  },
  "recommendation": "selective",
  "dissent": "Payload favors complete images; event filtering risks missed weak anomalies.",
  "sensitivities": "Recommendation depends on assumed science utility scores; weights editable before selection.",
  "alternatives": [
    "wide",
    "selective"
  ],
  "score_basis": "Engineering estimate on a 0–5 ordinal scale"
}
```
Traceability: depends_on → concept-trade-analysis, evidenced_by → selection-trade-analysis

## Risk

### mission-risk: Latency, coverage, lifetime and cost remain unverified
Explicit assumption · accepted · Owner: systems
```json
{
  "cause": "Concept inputs lack detailed orbit, environmental and supplier analysis",
  "event": "Mission cannot satisfy user constraints",
  "consequence": "Concept redesign",
  "likelihood": "medium",
  "severity": "high",
  "mitigation": "Complete access, radiation, reliability and cost studies",
  "residual_risk": "open"
}
```
Traceability: depends_on → req-latency, depends_on → req-life, depends_on → req-cost

## ReviewFinding

### wide-conflict: Payload production exceeds daily downlink capacity
Explicit assumption · resolved · Owner: systems
```json
{
  "severity": "critical",
  "resolution": "Selected selective; rejected candidate and payload dissent preserved in trade",
  "disciplines": [
    "Payload: preserve contextual imagery",
    "Bus & Ground: finite contact capacity"
  ]
}
```
Traceability: depends_on → wide-link, depends_on → wide-data

### review-latency: Daily downlink capacity does not establish 30-minute delivery
Explicit assumption · verified · Owner: review
```json
{
  "severity": "critical",
  "resolution": "Removed implied latency feasibility; allocated explicit verification task and retained mission risk. This resolves the evidence representation defect, not mission feasibility.",
  "entry_criteria": "Requirements approved; two concepts analyzed; selection recorded",
  "checks": [
    "Latency evidence",
    "Traceability",
    "Resource compliance"
  ],
  "exit_criteria": "Explicit unverified status, verification allocation and human acknowledgement",
  "reviewer_verification": "review: verification obligation and residual risk present; conceptual scope only"
}
```
Traceability: depends_on → req-latency, depends_on → selective-link

## VerificationItem

### verify-latency: Demonstrate worst-case acquisition-to-user latency
Explicit assumption · accepted · Owner: systems
```json
{
  "method": "Orbit access and processing simulation",
  "success_criterion": "All required acquisitions delivered within 30 minutes",
  "status": "not verified",
  "evidence": "Unknown: no propagated access evidence",
  "review_point": "Before preliminary design review"
}
```
Traceability: depends_on → req-latency, depends_on → operations

## Decision

### 567b6fd6-b15a-4f6c-81db-27fe6275cd61: Accept assumptions
Human decision · accepted · Owner: human
```json
{
  "rationale": "Simulated human acceptance for reproducible test fixture",
  "alternatives": [
    "accept",
    "reject",
    "challenge"
  ],
  "consequences": "Proposal e012781b-c8c5-4011-b6a4-adac3b0211bd accepted",
  "context": "Mission & Science proposes assumptions from the current engineering model"
}
```
Traceability: 

### 4ebf2af6-698a-429f-9312-f9cb16ad41d3: Accept requirements
Human decision · accepted · Owner: human
```json
{
  "rationale": "Simulated human acceptance for reproducible test fixture",
  "alternatives": [
    "accept",
    "reject",
    "challenge"
  ],
  "consequences": "Proposal 50c421ab-aa35-4a4c-838e-860670709b66 accepted",
  "context": "Mission & Science proposes requirements from the current engineering model"
}
```
Traceability: 

### 2704fc03-c8c0-4c06-839b-a2491b7bf903: Accept architectures
Human decision · accepted · Owner: human
```json
{
  "rationale": "Simulated human acceptance for reproducible test fixture",
  "alternatives": [
    "accept",
    "reject",
    "challenge"
  ],
  "consequences": "Proposal 9ae97e64-de6e-4952-aa06-5bd4f3eb0cf7 accepted",
  "context": "Systems Engineering proposes architectures from the current engineering model"
}
```
Traceability: 

### selection: Mission owner selected selective
Human decision · accepted · Owner: human
```json
{
  "rationale": "Simulated human selection: positive capacity with acknowledged science dissent",
  "alternatives": [
    "wide",
    "selective"
  ],
  "consequences": "Proceed to independent concept review; feasibility remains preliminary"
}
```
Traceability: depends_on → trade, depends_on → selective-link

### baseline-approval: Reference conceptual baseline — test fixture
Human decision · accepted · Owner: human
```json
{
  "rationale": "Approve conceptual study with explicitly unverified latency, coverage, lifetime and programme estimates",
  "alternatives": [
    "approve conceptual baseline",
    "continue engineering"
  ],
  "consequences": "Immutable concept snapshot; not flight feasibility approval"
}
```
Traceability: depends_on → selection, depends_on → review-latency, depends_on → mission-risk

## Traceability summary
101 typed relationships.
Calculated budgets link to versioned tool executions. Requirements trace to the mission objective.