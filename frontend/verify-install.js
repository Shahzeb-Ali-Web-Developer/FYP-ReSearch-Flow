// Quick verification script
const fs = require('fs');
const path = require('path');

const cytoscapePath = path.join(__dirname, 'node_modules', 'cytoscape', 'package.json');
const dagrePath = path.join(__dirname, 'node_modules', 'cytoscape-dagre', 'package.json');

console.log('Checking cytoscape installation...\n');

if (fs.existsSync(cytoscapePath)) {
  const pkg = JSON.parse(fs.readFileSync(cytoscapePath, 'utf8'));
  console.log('✅ cytoscape: INSTALLED');
  console.log(`   Version: ${pkg.version}`);
} else {
  console.log('❌ cytoscape: NOT INSTALLED');
  console.log('   Run: npm install cytoscape@3.32.0 --save');
}

if (fs.existsSync(dagrePath)) {
  const pkg = JSON.parse(fs.readFileSync(dagrePath, 'utf8'));
  console.log('✅ cytoscape-dagre: INSTALLED');
  console.log(`   Version: ${pkg.version}`);
} else {
  console.log('❌ cytoscape-dagre: NOT INSTALLED');
  console.log('   Run: npm install cytoscape-dagre@2.5.0 --save');
}

console.log('\nIf packages are missing, run:');
console.log('  npm install cytoscape@3.32.0 cytoscape-dagre@2.5.0 --save');
