import json

workflow = {
  "id": "enrich_apollo_workflow_1",
  "active": True,
  "name": "enrich_apollo",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "enrich_apollo",
        "options": {}
      },
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [0, 0]
    },
    {
      "parameters": {
        "url": "http://backend:8000/internal/apollo-accounts/available",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Internal-Key",
              "value": "8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA"
            }
          ]
        },
        "options": {}
      },
      "name": "Get Apollo Account",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [200, 0]
    },
    {
      "parameters": {
        "url": "=http://backend:8000/internal/campaigns/{{$(\"Webhook\").first().json.body.campaign_id}}/companies/cleaned",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Internal-Key",
              "value": "8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA"
            }
          ]
        },
        "options": {}
      },
      "name": "Get Cleaned Companies",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [400, 0]
    },
    {
      "parameters": {
        "jsCode": "const companies = $input.first().json;\nif (!Array.isArray(companies) || companies.length === 0) return [];\nreturn companies.map(c => ({ json: c }));"
      },
      "name": "Split Companies",
      "type": "n8n-nodes-base.code",
      "typeVersion": 1,
      "position": [600, 0]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=https://httpbin.org/post?token={{ $(\"Get Apollo Account\").first().json.api_key }}",
        "sendBody": True,
        "bodyParameters": {
          "parameters": [
            {
              "name": "domain",
              "value": "={{$json.website}}"
            }
          ]
        },
        "options": {}
      },
      "name": "Mock Apollo API (Run)",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [800, 0],
      "notesInFlow": True,
      "notes": "MOCKED. Replace with real Apollo contact search API later."
    },
    {
      "parameters": {
        "jsCode": "return $input.all().map((item, i) => {\n  const company = $(\"Split Companies\").all()[i].json;\n  return {\n    json: {\n      company_id: company.id,\n      first_name: \"Jane\",\n      last_name: \"Doe\",\n      email: \"jane@\" + company.website,\n      position: \"CEO\"\n    }\n  };\n});"
      },
      "name": "Mock Apollo Results",
      "type": "n8n-nodes-base.code",
      "typeVersion": 1,
      "position": [1000, 0]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://backend:8000/internal/contacts/bulk",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Internal-Key",
              "value": "8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={\n  \"company_id\": \"{{ $json.company_id }}\",\n  \"contacts\": [\n    {\n      \"first_name\": \"{{ $json.first_name }}\",\n      \"last_name\": \"{{ $json.last_name }}\",\n      \"email\": \"{{ $json.email }}\",\n      \"position\": \"{{ $json.position }}\"\n    }\n  ]\n}",
        "options": {}
      },
      "name": "POST Contacts",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1200, 0]
    },
    {
      "parameters": {
        "jsCode": "return [{ json: { campaign_id: $(\"Webhook\").first().json.body.campaign_id, job_id: $(\"Webhook\").first().json.body.job_id } }];"
      },
      "name": "Merge To Single Item",
      "type": "n8n-nodes-base.code",
      "typeVersion": 1,
      "position": [1400, 0]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=http://backend:8000/internal/jobs/{{ $json.job_id }}/status",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Internal-Key",
              "value": "8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={\n  \"status\": \"SUCCESS\"\n}",
        "options": {}
      },
      "name": "POST Job Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1600, 0]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "=http://backend:8000/internal/campaigns/{{ $json.campaign_id }}/status",
        "sendHeaders": True,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-Internal-Key",
              "value": "8U_trjGVldURORde98O5CmksUTVduWJVkLXKlgQ70kq8T8_SJkldr3oFtECsytL4IojuEayVYwIjUQ7QuEh_CA"
            },
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={\n  \"status\": \"COMPLETED\"\n}",
        "options": {}
      },
      "name": "POST Campaign Status",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 3,
      "position": [1800, 0]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Get Apollo Account",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get Apollo Account": {
      "main": [
        [
          {
            "node": "Get Cleaned Companies",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get Cleaned Companies": {
      "main": [
        [
          {
            "node": "Split Companies",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Split Companies": {
      "main": [
        [
          {
            "node": "Mock Apollo API (Run)",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Mock Apollo API (Run)": {
      "main": [
        [
          {
            "node": "Mock Apollo Results",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Mock Apollo Results": {
      "main": [
        [
          {
            "node": "POST Contacts",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "POST Contacts": {
      "main": [
        [
          {
            "node": "Merge To Single Item",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Merge To Single Item": {
      "main": [
        [
          {
            "node": "POST Job Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "POST Job Status": {
      "main": [
        [
          {
            "node": "POST Campaign Status",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {}
}

with open("n8n/workflows/enrich_apollo.json", "w") as f:
    json.dump(workflow, f, indent=2)
