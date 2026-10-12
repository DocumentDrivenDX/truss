import {decodeCandidatePublicationClaim} from '../../packages/postgresql/src/security-claim-observation';
console.log(JSON.stringify(decodeCandidatePublicationClaim(await Bun.stdin.json())));
