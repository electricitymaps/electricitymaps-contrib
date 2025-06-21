const PATTERN = {
  identifier: /^[A-Za-z_$][A-Za-z0-9_$]*$/,
  digit: /^\d+$/,
};

const Object_hasOwnProperty = globalThis.Object.prototype.hasOwnProperty;

const notfound = Symbol.for('i18next-codemod/NotFound');

const isComposite = (u) => !!u && typeof u === 'object';

function hasOwn(u, key) {
  return !isComposite(u)
    ? typeof u === 'function' && key in u
    : typeof key === 'symbol'
    ? isComposite(u) && key in u
    : Object_hasOwnProperty.call(u, key);
}

function get(x, ks) {
  let out = x;
  let k;
  while ((k = ks.shift()) !== undefined) {
    if (hasOwn(out, k)) void (out = out[k]);
    else if (k === '') continue;
    else return notfound;
  }
  return out;
}

const isKey = (u) =>
  typeof u === 'symbol' || typeof u === 'number' || typeof u === 'string';

function parsePath(xs) {
  return Array.isArray(xs) && xs.every(isKey)
    ? [xs, () => true]
    : [xs.slice(0, -1), xs[xs.length - 1]];
}

function has(...args) {
  return (u) => {
    const [path, check] = parsePath(args);
    const got = get(u, path);
    return got !== notfound && check(got);
  };
}

function isStringLiteralNode(x) {
  return has('type', (type) => type === 'StringLiteral')(x);
}

function isTemplateLiteralNode(x) {
  return has('type', (type) => type === 'TemplateLiteral')(x);
}

function isMemberExpressionNode(x) {
  return has('type', (type) => type === 'MemberExpression')(x);
}

function isIdentifierNode(x) {
  return has('type', (type) => type === 'Identifier')(x);
}

function isArrayExpressionNode(x) {
  return has('type', (type) => type === 'ArrayExpression')(x);
}

function isObjectExpressionNode(x) {
  return has('type', (type) => type === 'ObjectExpression')(x);
}

function isCallExpressionNode(x) {
  return has('type', (type) => type === 'CallExpression')(x);
}

function isObjectPatternNode(x) {
  return has('type', (type) => type === 'ObjectPattern')(x);
}

function keyToSelector(key, j) {
  const path = key.split('.');
  const expr = path.reduce((acc, part) => {
    if (PATTERN.digit.test(part))
      return j.memberExpression(acc, j.literal(Number(part)), true);
    else if (PATTERN.identifier.test(part))
      return j.memberExpression(acc, j.identifier(part));
    else return j.memberExpression(acc, j.literal(part), true);
  }, j.identifier('$'));
  return j.arrowFunctionExpression([j.identifier('$')], expr);
}

function separateNamespaceFromPath(key) {
  const [head, ...tail] = key.split(':');
  return tail.length ? { ns: head, path: tail.join(':') } : { path: head };
}

function templateLiteralToTokens(template) {
  let tokens = [];
  template.quasis.forEach((quasi, i) => {
    if (quasi.value.cooked) {
      quasi.value.cooked.split('.').forEach((s) => {
        if (s) tokens.push(s);
      });
    }
    if (i < template.expressions.length) {
      tokens.push(template.expressions[i]);
    }
  });
  return tokens;
}

function tokensToSelector(tokens, j) {
  return tokens.reduce((acc, token) => {
    if (typeof token === 'string')
      if (PATTERN.digit.test(token))
        return j.memberExpression(acc, j.literal(Number(token)), true);
      else if (PATTERN.identifier.test(token))
        return j.memberExpression(acc, j.identifier(token));
      else return j.memberExpression(acc, j.literal(token), true);
    else return j.memberExpression(acc, token, true);
  }, j.identifier('$'));
}

/**
 * TODO: See if jscodeshift has native utilities for cloning AST nodes (since
 * {@link globalThis.structuredClone `structuredClone`} doesn't work here).
 */
function clone(node) {
  return JSON.parse(JSON.stringify(node));
}

function is18nextTFunction(callee, { tAliases, i18nAliases }) {
  return (
    (isIdentifierNode(callee) && tAliases.has(callee.name)) ||
    (isMemberExpressionNode(callee) &&
      !callee.computed &&
      isIdentifierNode(callee.property) &&
      callee.property.name === 't' &&
      isIdentifierNode(callee.object) &&
      i18nAliases.has(callee.object.name))
  );
}

module.exports = function transform(file, api) {
  const j = api.jscodeshift;
  const root = j(file.source);

  const i18nAliases = new Set();
  const tAliases = new Set();
  const useTranslationAliases = new Set();
  const context = {
    i18nAliases,
    tAliases,
  };

  root.find(j.ImportDeclaration, { source: { value: 'i18next' } }).forEach((p) => {
    (p.node.specifiers || []).forEach((s) => {
      switch (s.type) {
        case 'ImportDefaultSpecifier':
        case 'ImportNamespaceSpecifier': {
          if (s.local == null) return;
          else i18nAliases.add(s.local.name);
          break;
        }
        case 'ImportSpecifier':
          if (s.imported.name === 't') tAliases.add(s.local ? s.local.name : 't');
          break;
      }
    });
  });

  root.find(j.ImportDeclaration, { source: { value: 'react-i18next' } }).forEach((p) => {
    (p.node.specifiers || []).forEach((s) => {
      if (s.type === 'ImportSpecifier' && s.imported.name === 'useTranslation') {
        useTranslationAliases.add(s.local ? s.local.name : 'useTranslation');
      }
    });
  });

  if (i18nAliases.size === 0 && tAliases.size === 0 && useTranslationAliases.size === 0)
    return file.source;

  root.find(j.VariableDeclarator).forEach((p) => {
    const init = p.node.init;
    const id = p.node.id;

    /**
     * @example
     * const { t } = useTranslation()
     */
    if (
      isObjectPatternNode(id) &&
      isCallExpressionNode(init) &&
      isIdentifierNode(init.callee) &&
      useTranslationAliases.has(init.callee.name)
    ) {
      id.properties.forEach((prop) => {
        if (
          has('value', isIdentifierNode)(prop) &&
          (has('key', 'name', (name) => name === 't')(prop) ||
            has('key', 'value', (value) => value === 't')(prop))
        ) {
          tAliases.add(prop.value.name);
        }
      });
    }

    /**
     * @example
     * const t = useTranslation().t
     */
    if (
      isIdentifierNode(id) &&
      isMemberExpressionNode(init) &&
      isCallExpressionNode(init.object) &&
      isIdentifierNode(init.object.callee) &&
      useTranslationAliases.has(init.object.callee.name) &&
      isIdentifierNode(init.property) &&
      init.property.name === 't'
    ) {
      tAliases.add(id.name);
    }
  });

  root
    .find(j.CallExpression)
    .filter((p) => is18nextTFunction(p.node.callee, context))
    .forEach((p) => {
      const { node } = p;
      const [arg0, arg1, arg2] = node.arguments;

      if (
        isArrayExpressionNode(arg0) &&
        arg0.elements.length > 0 &&
        arg0.elements.every(isStringLiteralNode)
      ) {
        const keys = arg0.elements.map((el) => el?.value);

        /** Gather default value + extra option props (if any) */
        let positionalDefaultValue = null;
        let optionsObject = null;
        if (isStringLiteralNode(arg1)) positionalDefaultValue = arg1;
        if (isObjectExpressionNode(arg1)) optionsObject = arg1;
        if (!optionsObject && isObjectExpressionNode(arg2)) optionsObject = arg2;

        /** options object properties (e.g., context, val, etc., but NOT defaultValue) */
        let toplevelOptionProperties = Array.of();
        /** case: defaultValue passed in the options object */
        let defaultValueFromOptions = null;
        if (optionsObject) {
          optionsObject.properties.forEach((prop) => {
            if (has('key')(prop) && has('value')(prop)) {
              const { key, value } = prop;
              if (has('name', (name) => typeof name === 'string')(key)) {
                const k = key.name || value;
                if (k === 'defaultValue') {
                  defaultValueFromOptions = prop.value;
                } else {
                  toplevelOptionProperties.push(prop);
                }
              }
            }
          });
        }

        const finalDefault = defaultValueFromOptions || positionalDefaultValue;

        const calleeClone = clone(node.callee);

        /** Recursively build nested t() calls */
        const buildCall = (idx) => {
          const { ns, path } = separateNamespaceFromPath(keys[idx]);

          const props = [];

          if (ns) props.push(j.property('init', j.identifier('ns'), j.literal(ns)));

          if (idx < keys.length - 1) {
            props.push(
              j.property('init', j.identifier('defaultValue'), buildCall(idx + 1))
            );
          } else if (finalDefault) {
            props.push(j.property('init', j.identifier('defaultValue'), finalDefault));
          }

          /** top-level props (besides nested default values) bubble up to the root selector */
          if (idx === 0 && toplevelOptionProperties.length) {
            props.push(...toplevelOptionProperties);
          }

          const args = [keyToSelector(path, j)];
          if (props.length) args.push(j.objectExpression(props));

          return j.callExpression(clone(calleeClone), args);
        };

        /** Replace the entire original call */
        j(p).replaceWith(buildCall(0));
        /** return so we don't fall through and start evaluating other branches */
        return;
      }

      root
        .find(j.CallExpression)
        .filter((p) => is18nextTFunction(p.node.callee, context))
        .forEach((p) => {
          const { node } = p;
          const [arg0, arg1, arg2] = p.node.arguments;

          /** case: dynamic-key */
          if (
            isTemplateLiteralNode(arg0) ||
            isIdentifierNode(arg0) ||
            isMemberExpressionNode(arg0)
          ) {
            /* derive selector function */
            const tokens = isTemplateLiteralNode(arg0)
              ? templateLiteralToTokens(arg0)
              : [arg0];
            const selectorFn = j.arrowFunctionExpression(
              [j.identifier('$')],
              tokensToSelector(tokens, j)
            );

            const newArgs = [selectorFn];
            const opts = {};

            /** positional defaultValue (string) */
            if (isStringLiteralNode(arg1)) opts.defaultValue = arg1;

            /** object‑style options (2nd or 3rd arg) */
            const optObj = [arg1, arg2].find((a) => a && a.type === 'ObjectExpression');
            if (optObj) {
              optObj.properties.forEach((prop) => {
                if (has('key')(prop) && has('value')(prop)) {
                  const { key, value } = prop;
                  if (has('name', (name) => typeof name === 'string')(key)) {
                    opts[key.name] = value;
                  } else if (has('value', (value) => typeof value === 'string')(key)) {
                    opts[key.value] = value;
                  }
                }
              });
            }

            if (Object.keys(opts).length) {
              newArgs.push(
                j.objectExpression(
                  Object.entries(opts).map(([k, v]) =>
                    j.property('init', j.identifier(k), v)
                  )
                )
              );
            }

            node.arguments = newArgs;
            /** return so we don't fall through and start evaluating other branches */
            return;
          }
        });

      if (!isStringLiteralNode(arg0) || typeof arg0.value !== 'string') return;

      const { ns, path } = separateNamespaceFromPath(arg0.value);
      const selectorFn = keyToSelector(path, j);
      const newArgs = [selectorFn];
      const opts = {};

      if (isStringLiteralNode(arg1)) opts.defaultValue = arg1;

      const optObj = [arg1, arg2].find(isObjectExpressionNode);
      if (optObj) {
        optObj.properties.forEach((prop) => {
          if (has('key')(prop) && has('value')(prop)) {
            const { key, value } = prop;
            if (has('name', (name) => typeof name === 'string')(key)) {
              opts[key.name] = value;
            } else if (has('value', (value) => typeof value === 'string')(key)) {
              opts[key.value] = value;
            }
          }
        });
      }

      if (ns && !('ns' in opts)) opts.ns = j.literal(ns);
      if (Object.keys(opts).length) {
        newArgs.push(
          j.objectExpression(
            Object.entries(opts).map(([k, v]) => j.property('init', j.identifier(k), v))
          )
        );
      }

      node.arguments = newArgs;
    });

  return root.toSource();
};
