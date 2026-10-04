// The only loaded code is KageX code and its locked dependencies. Source and
// eslint/tsconfig/package files from the repository never configure this tool.
import fs from 'node:fs';
import path from 'node:path';
import { Linter } from 'eslint';
import { Project, ts } from 'ts-morph';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const project = new Project({ useInMemoryFileSystem: true, skipAddingFilesFromTsConfig: true,
  skipFileDependencyResolution: true, compilerOptions: { noLib: true, noResolve: true, allowJs: true } });
const linter = new Linter();
const entities = [], warnings = [];
for (const relative of manifest.paths) {
  let source;
  try { source = new TextDecoder('utf-8', { fatal: true }).decode(fs.readFileSync(path.join(manifest.root, relative))); }
  catch { warnings.push({ code: 'FILE_PARSE_FAILED', relative_path: relative }); continue; }
  const file = project.createSourceFile('/' + relative, source, { overwrite: true });
  // Compiler syntax diagnostics only: no dependency resolution or emit.
  if (project.getProgram().compilerObject.getSyntacticDiagnostics(file.compilerNode).length) {
    warnings.push({ code: 'FILE_PARSE_FAILED', relative_path: relative }); file.forget(); continue;
  }
  let functions = 0, classes = 0, imports = 0, decisions = 0;
  const dependencies = new Set();
  function visit(node) {
    if (ts.isFunctionLike(node) && node.body) functions++;
    if (ts.isClassDeclaration(node) || ts.isClassExpression(node)) classes++;
    if (ts.isIfStatement(node) || ts.isConditionalExpression(node) || ts.isForStatement(node) ||
        ts.isForInStatement(node) || ts.isForOfStatement(node) || ts.isWhileStatement(node) ||
        ts.isDoStatement(node) || ts.isCatchClause(node) || ts.isCaseClause(node)) decisions++;
    if (ts.isBinaryExpression(node) && [ts.SyntaxKind.AmpersandAmpersandToken, ts.SyntaxKind.BarBarToken, ts.SyntaxKind.QuestionQuestionToken].includes(node.operatorToken.kind)) decisions++;
    let dependency;
    if (ts.isImportDeclaration(node) || (ts.isExportDeclaration(node) && node.moduleSpecifier)) {
      imports++; dependency = node.moduleSpecifier;
    } else if (ts.isCallExpression(node) && ((ts.isIdentifier(node.expression) && node.expression.text === 'require') || node.expression.kind === ts.SyntaxKind.ImportKeyword)) {
      imports++; dependency = node.arguments[0];
    } else if (ts.isImportEqualsDeclaration(node) && ts.isExternalModuleReference(node.moduleReference)) {
      imports++; dependency = node.moduleReference.expression;
    }
    if (dependency && ts.isStringLiteral(dependency)) dependencies.add(dependency.text);
    ts.forEachChild(node, visit);
  }
  visit(file.compilerNode);
  const lines = source.split(/\r\n|\n|\r/);
  if (lines.at(-1) === '') lines.pop();
  const metrics = { loc: lines.length, num_functions: functions, num_classes: classes,
    import_count: imports, coupling: dependencies.size };
  if (manifest.language === 'javascript') {
    // Linter receives source text and a fixed config; no config discovery,
    // processors, repository plugins, inline overrides or filesystem API.
    const messages = linter.verify(source, { languageOptions: { ecmaVersion: 2025,
      sourceType: relative.endsWith('.cjs') ? 'commonjs' : 'module', parserOptions: { ecmaFeatures: { jsx: true } } },
      linterOptions: { noInlineConfig: true }, rules: { complexity: ['error', { max: 0, variant: 'classic' }] } });
    if (messages.some(message => message.fatal)) {
      warnings.push({ code: 'FILE_PARSE_FAILED', relative_path: relative }); file.forget(); continue;
    }
    const complexities = messages.filter(message => message.ruleId === 'complexity').map(message => {
      const match = message.message.match(/complexity of (\d+)/);
      if (!match) throw new Error('Unexpected pinned ESLint result');
      return Number(match[1]);
    });
    metrics.cyclomatic_complexity = complexities.reduce((sum, value) => sum + value, 0);
    metrics.max_function_complexity = Math.max(0, ...complexities);
    metrics.complexity_units = complexities.length;
  } else {
    // TS-specific structural count, intentionally not labeled ESLint complexity.
    metrics.decision_count = decisions;
  }
  entities.push({ language: manifest.language, entity_type: 'file', relative_path: relative,
    qualified_name: relative, start_line: 1, end_line: Math.max(1, lines.length), metrics,
    analyzer_name: manifest.language === 'javascript' ? 'eslint+ts-morph' : 'ts-morph',
    analyzer_version: `eslint-${Linter.version}/ts-morph-${require('ts-morph/package.json').version}/typescript-${ts.version}/node-${process.versions.node}`,
    metric_schema_version: manifest.language === 'javascript' ? 'javascript_file_v1' : 'typescript_file_v1', warnings: [] });
  file.forget();
}
process.stdout.write(JSON.stringify({ entities, warnings }));
