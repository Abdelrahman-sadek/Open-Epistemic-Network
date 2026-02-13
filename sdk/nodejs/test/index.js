import OpenEpistemicClient from '../src/index.js';
import { expect } from 'chai';

describe('OpenEpistemicClient', () => {
    let client;

    before(() => {
        client = new OpenEpistemicClient('http://localhost:8000');
    });

    describe('Health Check', () => {
        it('should return health status', async () => {
            const health = await client.getHealth();
            expect(health).to.be.an('object');
            expect(health.status).to.equal('ok');
        });
    });

    describe('Validator Operations', () => {
        let validatorId;
        const testPublicKey = 'test-key-' + Date.now();
        const testModelFamily = 'test-model';
        const testRegion = 'test-region';
        const testDomainFocus = 'test-domain';

        it('should register a validator', async () => {
            const result = await client.registerValidator(
                testPublicKey,
                testModelFamily,
                testRegion,
                testDomainFocus
            );
            
            expect(result).to.be.an('object');
            expect(result).to.have.property('id');
            validatorId = result.id;
            
            expect(result.public_key).to.equal(testPublicKey);
            expect(result.model_family).to.equal(testModelFamily);
            expect(result.region).to.equal(testRegion);
            expect(result.domain_focus).to.equal(testDomainFocus);
        });

        it('should get validator information', async () => {
            const validator = await client.getValidator(validatorId);
            expect(validator).to.be.an('object');
            expect(validator.id).to.equal(validatorId);
            expect(validator.public_key).to.equal(testPublicKey);
        });
    });

    describe('Claim Operations', () => {
        let claimId;
        const testStatement = 'Test claim ' + Date.now();
        const testDomain = 'test-domain';
        const testProposerId = 'test-proposer-' + Date.now();

        it('should submit a claim', async () => {
            const result = await client.submitClaim(
                testStatement,
                testDomain,
                testProposerId,
                ['https://example.com/evidence']
            );
            
            expect(result).to.be.an('object');
            expect(result).to.have.property('id');
            claimId = result.id;
            
            expect(result.statement).to.equal(testStatement);
            expect(result.domain).to.equal(testDomain);
            expect(result.proposer_id).to.equal(testProposerId);
        });

        it('should get claim information', async () => {
            const claim = await client.getClaim(claimId);
            expect(claim).to.be.an('object');
            expect(claim.id).to.equal(claimId);
            expect(claim.statement).to.equal(testStatement);
        });
    });

    describe('Governance Operations', () => {
        it('should get governance parameters', async () => {
            const params = await client.getGovernanceParams();
            expect(params).to.be.an('object');
            expect(params).to.have.property('version');
            expect(params).to.have.property('parameters');
        });
    });

    describe('Ledger Operations', () => {
        it('should get ledger root', async () => {
            const root = await client.getLedgerRoot();
            expect(root).to.be.an('object');
            expect(root).to.have.property('merkle_root');
            expect(root.merkle_root).to.be.a('string');
        });
    });
});