#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const minimist = require('minimist');
const chalk = require('chalk');
const util = require('util');
const exec = util.promisify(require('child_process').exec);
const { version } = require('./package.json');

const usage = `  Usage: prisma-admin PRSIMA_ENDPOINT
  ${chalk.bold('Starts a admin server for the given prisma endpoint')}
  Options:
    --token, -t    Add a custom header (ex. 'X-API-KEY=ABC123'), can be used multiple times
    --version, -v   Print version of prisma-admin
  Example:
  ${chalk.yellow(
		'prisma-admin https://eu1.prisma.sh/lol/homepage-snippets/dev',
  )}
`;

async function main() {
	const argv = minimist(process.argv.slice(2));

	if (argv['version'] || argv['v']) {
		console.log(version);
		process.exit(0);
	}

	if (argv._.length < 1) {
		console.log(usage);
		return;
	}

	const endpoint = argv._[0];
	const token = argv['token'] || argv['t'];
	let envString = `window.env={ PRISMA_ENDPOINT: "${endpoint}" };`;
	if (token) {
		envString = `${envString}window.env.PRISMA_TOKEN="${token}"`;
	}

	fs.writeFileSync(path.resolve(__dirname, './build/runtime-env.js'), envString, 'utf8');

	console.log(chalk.green('App running at port 5000'));
	exec('yarn serve', { cwd: __dirname });
}

main().catch(e => console.log(e));