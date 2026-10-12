import {decodeCandidateAuthorityGuard} from '../../packages/postgresql/src/security-guard-observation';
console.log(JSON.stringify(decodeCandidateAuthorityGuard(await Bun.stdin.json())));
