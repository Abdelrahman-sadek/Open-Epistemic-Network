import axios from 'axios';

class OpenEpistemicClient {
    constructor(baseUrl = "http://localhost:8000", timeout = 10000) {
        this.client = axios.create({
            baseURL: baseUrl,
            timeout: timeout,
        });
    }

    // Validators
    async registerValidator(publicKey, modelFamily, region, domainFocus = null) {
        const payload = {
            public_key: publicKey,
            model_family: modelFamily,
            region: region,
            domain_focus: domainFocus,
        };
        
        const response = await this.client.post("/validators", payload);
        return response.data;
    }

    async getValidator(validatorId) {
        const response = await this.client.get(`/validators/${validatorId}`);
        return response.data;
    }

    // Claims
    async submitClaim(statement, domain, proposerId, evidenceRefs = []) {
        const payload = {
            statement: statement,
            domain: domain,
            proposer_id: proposerId,
            evidence_refs: evidenceRefs,
        };
        
        const response = await this.client.post("/claims", payload);
        return response.data;
    }

    async getClaim(claimId) {
        const response = await this.client.get(`/claims/${claimId}`);
        return response.data;
    }

    // Votes
    async submitVote(claimId, validatorId, voteType, confidence, signature, timestamp = null) {
        const payload = {
            claim_id: claimId,
            validator_id: validatorId,
            vote_type: voteType,
            confidence: confidence,
            timestamp: timestamp || new Date().toISOString(),
            signature: signature,
        };
        
        const response = await this.client.post("/votes", payload);
        return response.data;
    }

    async getVotesForClaim(claimId) {
        const response = await this.client.get(`/claims/${claimId}/votes`);
        return response.data;
    }

    // Consensus
    async getConsensusForClaim(claimId) {
        const response = await this.client.get(`/validation/claims/${claimId}/consensus`);
        return response.data;
    }

    // Governance
    async getGovernanceParams() {
        const response = await this.client.get("/governance/params");
        return response.data;
    }

    async createGovernanceProposal(title, body, parametersDiff = {}, activationDelayHours = 24) {
        const payload = {
            title: title,
            body: body,
            parameters_diff: parametersDiff,
            activation_delay_hours: activationDelayHours,
        };
        
        const response = await this.client.post("/governance/proposals", payload);
        return response.data;
    }

    // Ledger
    async getLedgerRoot() {
        const response = await this.client.get("/ledger/root");
        return response.data;
    }

    // Health
    async getHealth() {
        const response = await this.client.get("/health");
        return response.data;
    }
}

export default OpenEpistemicClient;