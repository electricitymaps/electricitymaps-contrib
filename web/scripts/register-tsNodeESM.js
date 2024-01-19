/**
 * This script is meant to be used with 'node --import=register-tsNodeESM.js', and allows
 * node v20 to use ts-node to execute Typescript files that contain ESM modules, without
 * outputting JS files.
 */
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';
register('ts-node/esm', pathToFileURL('./'));
