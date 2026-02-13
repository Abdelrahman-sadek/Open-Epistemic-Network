use reqwest::Client as HttpClient;
use serde::{Deserialize, Serialize};
use thiserror::Error;
use std::time::Duration;

#[derive(Debug, Error)]
pub enum OpenEpistemicError {
    #[error("HTTP request failed: {0}")]
    HttpRequest(#[from] reqwest::Error),
    #[error("Invalid response format: {0}")]
    InvalidResponse(String),
    #[error("API error: {0}")]
    ApiError(String),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Validator {
    pub id: String,
    pub public_key: String,
    pub model_family: String,
    pub region: String,
    pub domain_focus: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct RegisterValidatorRequest {
    pub public_key: String,
    pub model_family: String,
    pub region: String,
    pub domain_focus: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Claim {
    pub id: String,
    pub statement: String,
    pub domain: String,
    pub proposer_id: String,
    pub evidence_refs: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct SubmitClaimRequest {
    pub statement: String,
    pub domain: String,
    pub proposer_id: String,
    pub evidence_refs: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Vote {
    pub id: String,
    pub claim_id: String,
    pub validator_id: String,
    pub vote_type: String,
    pub confidence: f64,
    pub timestamp: String,
    pub signature: String,
}

#[derive(Debug, Serialize)]
pub struct SubmitVoteRequest {
    pub claim_id: String,
    pub validator_id: String,
    pub vote_type: String,
    pub confidence: f64,
    pub timestamp: String,
    pub signature: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ConsensusResponse {
    pub claim_id: String,
    pub round: i32,
    pub outcome: Option<String>,
    pub confidence: f64,
    pub created_at: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct GovernanceParams {
    pub version: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct CreateGovernanceProposalRequest {
    pub title: String,
    pub body: String,
    pub parameters_diff: serde_json::Value,
    pub activation_delay_hours: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LedgerRootResponse {
    pub merkle_root: String,
}

pub struct OpenEpistemicClient {
    base_url: String,
    client: HttpClient,
}

impl OpenEpistemicClient {
    pub fn new(base_url: Option<&str>) -> Self {
        let base_url = base_url.unwrap_or("http://localhost:8000").to_string();
        let client = HttpClient::builder()
            .timeout(Duration::from_secs(10))
            .build()
            .expect("Failed to create HTTP client");
            
        Self { base_url, client }
    }

    // Health
    pub async fn get_health(&self) -> Result<HealthResponse, OpenEpistemicError> {
        let url = format!("{}/health", self.base_url);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Health check failed with status: {}",
                response.status()
            )))
        }
    }

    // Validators
    pub async fn register_validator(
        &self,
        public_key: &str,
        model_family: &str,
        region: &str,
        domain_focus: Option<&str>,
    ) -> Result<Validator, OpenEpistemicError> {
        let url = format!("{}/validators", self.base_url);
        let request = RegisterValidatorRequest {
            public_key: public_key.to_string(),
            model_family: model_family.to_string(),
            region: region.to_string(),
            domain_focus: domain_focus.map(|s| s.to_string()),
        };
        
        let response = self.client.post(&url).json(&request).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Validator registration failed with status: {}",
                response.status()
            )))
        }
    }

    pub async fn get_validator(&self, validator_id: &str) -> Result<Validator, OpenEpistemicError> {
        let url = format!("{}/validators/{}", self.base_url, validator_id);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Get validator failed with status: {}",
                response.status()
            )))
        }
    }

    // Claims
    pub async fn submit_claim(
        &self,
        statement: &str,
        domain: &str,
        proposer_id: &str,
        evidence_refs: &[&str],
    ) -> Result<Claim, OpenEpistemicError> {
        let url = format!("{}/claims", self.base_url);
        let request = SubmitClaimRequest {
            statement: statement.to_string(),
            domain: domain.to_string(),
            proposer_id: proposer_id.to_string(),
            evidence_refs: evidence_refs.iter().map(|s| s.to_string()).collect(),
        };
        
        let response = self.client.post(&url).json(&request).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Claim submission failed with status: {}",
                response.status()
            )))
        }
    }

    pub async fn get_claim(&self, claim_id: &str) -> Result<Claim, OpenEpistemicError> {
        let url = format!("{}/claims/{}", self.base_url, claim_id);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Get claim failed with status: {}",
                response.status()
            )))
        }
    }

    // Votes
    pub async fn submit_vote(
        &self,
        claim_id: &str,
        validator_id: &str,
        vote_type: &str,
        confidence: f64,
        signature: &str,
        timestamp: Option<&str>,
    ) -> Result<Vote, OpenEpistemicError> {
        let url = format!("{}/votes", self.base_url);
        let request = SubmitVoteRequest {
            claim_id: claim_id.to_string(),
            validator_id: validator_id.to_string(),
            vote_type: vote_type.to_string(),
            confidence,
            timestamp: timestamp.map(|s| s.to_string()).unwrap_or_else(|| {
                chrono::Utc::now().to_rfc3339_opts(chrono::SecondsFormat::Secs, true)
            }),
            signature: signature.to_string(),
        };
        
        let response = self.client.post(&url).json(&request).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Vote submission failed with status: {}",
                response.status()
            )))
        }
    }

    pub async fn get_votes_for_claim(&self, claim_id: &str) -> Result<Vec<Vote>, OpenEpistemicError> {
        let url = format!("{}/claims/{}/votes", self.base_url, claim_id);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Get votes failed with status: {}",
                response.status()
            )))
        }
    }

    // Consensus
    pub async fn get_consensus_for_claim(&self, claim_id: &str) -> Result<ConsensusResponse, OpenEpistemicError> {
        let url = format!("{}/validation/claims/{}/consensus", self.base_url, claim_id);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Consensus request failed with status: {}",
                response.status()
            )))
        }
    }

    // Governance
    pub async fn get_governance_params(&self) -> Result<GovernanceParams, OpenEpistemicError> {
        let url = format!("{}/governance/params", self.base_url);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Governance params request failed with status: {}",
                response.status()
            )))
        }
    }

    pub async fn create_governance_proposal(
        &self,
        title: &str,
        body: &str,
        parameters_diff: &serde_json::Value,
        activation_delay_hours: i32,
    ) -> Result<serde_json::Value, OpenEpistemicError> {
        let url = format!("{}/governance/proposals", self.base_url);
        let request = CreateGovernanceProposalRequest {
            title: title.to_string(),
            body: body.to_string(),
            parameters_diff: parameters_diff.clone(),
            activation_delay_hours,
        };
        
        let response = self.client.post(&url).json(&request).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Governance proposal failed with status: {}",
                response.status()
            )))
        }
    }

    // Ledger
    pub async fn get_ledger_root(&self) -> Result<LedgerRootResponse, OpenEpistemicError> {
        let url = format!("{}/ledger/root", self.base_url);
        let response = self.client.get(&url).send().await?;
        
        if response.status().is_success() {
            Ok(response.json().await?)
        } else {
            Err(OpenEpistemicError::ApiError(format!(
                "Ledger root request failed with status: {}",
                response.status()
            )))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio_test;

    #[tokio_test::test]
    async fn test_health_check() {
        let client = OpenEpistemicClient::new(None);
        
        match client.get_health().await {
            Ok(health) => assert_eq!(health.status, "ok"),
            Err(e) => eprintln!("Health check failed: {}", e),
        }
    }

    #[tokio_test::test]
    async fn test_validator_registration() {
        let client = OpenEpistemicClient::new(None);
        let test_key = format!("test-key-{}", chrono::Utc::now().timestamp());
        
        match client.register_validator(
            &test_key,
            "test-model",
            "test-region",
            Some("test-domain"),
        ).await {
            Ok(validator) => {
                assert!(!validator.id.is_empty());
                assert_eq!(validator.public_key, test_key);
            }
            Err(e) => eprintln!("Validator registration failed: {}", e),
        }
    }

    #[tokio_test::test]
    async fn test_claim_submission() {
        let client = OpenEpistemicClient::new(None);
        let test_id = format!("test-claim-{}", chrono::Utc::now().timestamp());
        
        match client.submit_claim(
            &format!("Test claim {}", test_id),
            "test-domain",
            &format!("proposer-{}", test_id),
            &["https://example.com/evidence"],
        ).await {
            Ok(claim) => {
                assert!(!claim.id.is_empty());
                assert!(claim.statement.contains(&test_id));
            }
            Err(e) => eprintln!("Claim submission failed: {}", e),
        }
    }
}