
resource "google_pubsub_topic" "transactions" {
  name                       = "transactions"
  message_retention_duration = "86400s" 
}

resource "google_pubsub_subscription" "transactions_sub" {
  name                 = "transactions-sub"
  topic                = google_pubsub_topic.transactions.name
  ack_deadline_seconds = 60

  expiration_policy {
    ttl = "" 
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
}

resource "google_pubsub_topic" "budget_breaches_alerts" {
  name                       = "budget-breaches-alerts"
  message_retention_duration = "604800s" 
}

resource "google_pubsub_subscription" "budget_breaches_alerts_sub" {
  name                 = "budget-breaches-alerts-sub"
  topic                = google_pubsub_topic.budget_breaches_alerts.name
  ack_deadline_seconds = 30

  expiration_policy {
    ttl = "" 
  }
}
