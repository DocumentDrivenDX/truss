import {Buffer} from 'buffer/';
import {URL,URLSearchParams} from 'whatwg-url';
import clone from '@ungap/structured-clone';
import {sha256} from '@noble/hashes/sha2.js';
Object.assign(globalThis,{Buffer,URL,URLSearchParams,structuredClone:clone,__sha256:sha256});
