// SPDX-License-Identifier: MIT OR Apache-2.0
import {prepareCanonicalWireTree} from '../../../postgresql/src/canonical-wire-tree';
const wire=await Bun.stdin.bytes();
process.stdout.write(JSON.stringify(prepareCanonicalWireTree(wire)));
