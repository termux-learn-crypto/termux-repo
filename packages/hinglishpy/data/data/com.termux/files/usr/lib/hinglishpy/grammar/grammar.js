// Tree-sitter grammar for HinglishPy - Python-like syntax, Hinglish keywords
// Install: npm i -g tree-sitter-cli
// Build:   tree-sitter generate
// Test:    tree-sitter test
// Note: grammar ke liye build machine par tree-sitter-cli install karna hoga.

const PREC = {
  or: 1,
  and: 2,
  not: 3,
  compare: 4,
  pipe: 5,
  xor: 6,
  ampersand: 7,
  shift: 8,
  sum: 9,
  term: 10,
  unary_operator: 11,
  power: 12,
  await: 13,
  attribute: 14,
  call: 15,
  primary: 16,
};

module.exports = grammar({
  name: 'hinglishpy',

  extras: $ => [/[ \t\r\n]/, $.comment],

  word: $ => $.identifier,

  externals: $ => [$.INDENT, $.DEDENT, $.NEWLINE],

  conflicts: $ => [
    [$.capture_pattern, $.dotted_name],
    [$.atom, $.target_list_body],
  ],

  inline: $ => [
    $._simple_statement,
    $._expression,
  ],

  rules: {
    source_file: $ => repeat(choice(
      $._simple_statement,
      $._compound_statement,
    )),

    _simple_statement: $ => seq($._statement, $.NEWLINE),

    _statement: $ => choice(
      $.assignment,
      $.expression_statement,
      $.return_statement,
      $.yield_statement,
      $.break_statement,
      $.continue_statement,
      $.pass_statement,
      $.delete_statement,
      $.assert_statement,
      $.global_statement,
      $.nonlocal_statement,
      $.raise_statement,
      $.import_statement,
      $.from_import_statement,
      $.print_statement,
    ),

    assignment: $ => choice(
      seq(field('left', $._target_list), '=', field('right', $.expression_list)),
      seq(field('left', $._target_list), ':', field('annotation', $._expression), optional(seq('=', field('value', $._expression)))),
      seq(field('left', $._target_list), choice('+=', '-=', '*=', '/=', '//=', '%=', '**=', '@=', '&=', '|=', '^=', '<<=', '>>='), field('right', $._expression)),
    ),

    expression_statement: $ => $._expression,

    return_statement: $ => seq('wapas', optional($.expression_list)),

    yield_statement: $ => seq('batao', optional(choice(seq('se', $._expression), $.expression_list))),

    break_statement: $ => 'todo',
    continue_statement: $ => 'jaari',
    pass_statement: $ => 'chhodo',

    delete_statement: $ => seq('mitao', $._target_list),

    assert_statement: $ => seq('sach', $._expression, optional(seq(',', $._expression))),

    global_statement: $ => seq('baishvik', commaSep1($.identifier)),
    nonlocal_statement: $ => seq('asthaniye', commaSep1($.identifier)),

    raise_statement: $ => seq('badhao', optional(seq($._expression, optional(seq('se', $._expression))))),

    import_statement: $ => seq(
      'lao',
      commaSep1(choice(
        field('name', $.dotted_name),
        seq(field('name', $.dotted_name), 'jaise', field('alias', $.identifier)),
      )),
    ),

    from_import_statement: $ => seq(
      'se',
      optional('.'),
      optional($.dotted_name),
      'lao',
      choice(
        '*',
        commaSep1(choice(
          field('name', $.identifier),
          seq(field('name', $.identifier), 'jaise', field('alias', $.identifier)),
        )),
      ),
    ),

    print_statement: $ => seq('bolo', optional(commaSep1(choice($.starred_expression, $._expression)))),

    dotted_name: $ => commaJoinRepeat1([$.identifier, '.']),

    _compound_statement: $ => choice(
      $.if_statement,
      $.while_statement,
      $.for_statement,
      $.with_statement,
      $.try_statement,
      $.function_definition,
      $.class_definition,
      $.match_statement,
    ),

    if_statement: $ => seq(
      'agar', field('condition', $._expression),
      $.block,
      repeat(seq('nahito', field('condition', $._expression), $.block)),
      optional(seq('warna', $.block)),
    ),

    while_statement: $ => seq('jabtak', field('condition', $._expression), $.block, optional(seq('warna', $.block))),

    for_statement: $ => seq(
      optional('asink'),
      'har', field('target', $._target_list), 'me', field('iterable', $._expression),
      $.block,
      optional(seq('warna', $.block)),
    ),

    with_statement: $ => seq(
      optional('asink'),
      'saath',
      commaSep1(seq($._expression, optional(seq('jaise', $._target_list)))),
      $.block,
    ),

    try_statement: $ => seq(
      'koshish', $.block,
      repeat(seq('pakdo', optional('*'), optional(field('type', $._expression)), optional(seq('jaise', field('name', $.identifier))), $.block)),
      optional(seq('warna', $.block)),
      optional(seq('ant', $.block)),
    ),

    function_definition: $ => seq(
      optional($.decorators),
      optional('asink'),
      'kaam',
      field('name', $.identifier),
      field('parameters', $.parameters),
      optional(seq('->', field('return_type', $._expression))),
      $.block,
    ),

    class_definition: $ => seq(
      optional($.decorators),
      'varg',
      field('name', $.identifier),
      optional(seq('(', optional($.argument_list), ')')),
      $.block,
    ),

    decorators: $ => repeat1(seq('@', $._expression, '\n')),

    match_statement: $ => seq(
      'match', field('subject', $._expression),
      ':', $.NEWLINE,
      $.INDENT,
      repeat1($.case_clause),
      $.DEDENT,
    ),

    case_clause: $ => seq(
      'case', field('pattern', $._pattern), optional(seq('agar', field('guard', $._expression))),
      $.block,
    ),

    _pattern: $ => choice(
      $.literal_pattern,
      $.capture_pattern,
      $.wildcard,
      $.or_pattern,
      $.as_pattern,
      $.sequence_pattern,
      $.mapping_pattern,
      $.class_pattern,
      $.value_pattern,
      seq('(', $._pattern, ')'),
    ),

    literal_pattern: $ => choice($.number, $.string, 'sahi', 'galat', 'kuchnahi'),
    capture_pattern: $ => $.identifier,
    wildcard: $ => '_',
    value_pattern: $ => $.dotted_name,
    or_pattern: $ => prec.left(PREC.or, seq($._pattern, '|', $._pattern)),
    as_pattern: $ => seq($._pattern, 'jaise', $.identifier),
    sequence_pattern: $ => seq('[',
      optional(commaSep1(choice($._pattern, seq('*', field('rest', $.identifier))))),
      ']'),
    parenthesized_pattern: $ => seq('(', $._pattern, ')'),
    mapping_pattern: $ => seq(
      '{',
      optional(commaSep1(seq(choice($.string, $.number, $.identifier), ':', $._pattern))),
      optional(seq('**', field('rest', $.identifier))),
      '}',
    ),
    class_pattern: $ => seq($.dotted_name, '(',
      optional(commaSep1(choice(seq($.identifier, '=', $._pattern), $._pattern))),
      ')'),

    block: $ => seq(':', $.NEWLINE, $.INDENT, repeat1(choice($._simple_statement, $._compound_statement)), $.DEDENT),

    parameters: $ => seq('(',
      optional(commaSep1(choice(
        field('param', $.identifier),
        field('param', seq($.identifier, ':', $._expression)),
        seq($.identifier, '=', $._expression),
        seq('*', $.identifier),
        seq('**', $.identifier),
        '*',
        '/',
      ))),
      ')',
    ),

    // -------- Expressions (left-associative, precedence from PREC) --------
    _expression: $ => choice(
      $.conditional_expression,
      $.lambda_expression,
      $.or_expression,
    ),

    conditional_expression: $ => prec.right(PREC.or, seq($._expression, 'agar', $._expression, 'warna', $._expression)),

    lambda_expression: $ => prec.left(0, seq('banao', $.parameters, ':', $._expression)),

    or_expression: $ => prec.left(PREC.or, seq($.and_expression, repeat(seq('ya', $.and_expression)))),
    and_expression: $ => prec.left(PREC.and, seq($.not_expression, repeat(seq('aur', $.not_expression)))),
    not_expression: $ => choice(seq('nahi', $.not_expression), $.comparison_expression),

    comparison_expression: $ => prec.left(PREC.compare, seq($.arith_expr, repeat(choice(
      seq($.comp_op, $.arith_expr),
    )))),
    comp_op: $ => choice('<', '<=', '>', '>=', '==', '!=', 'me', seq('nahi', 'me'), 'hai', seq('hai', 'nahi')),

    arith_expr: $ => prec.left(PREC.sum, seq($._bitwise, repeat(seq(choice('+', '-'), $._bitwise)))),

    _bitwise: $ => choice(
      $.bitwise_or,
      $.bitwise_xor,
      $.bitwise_and,
      $.shift_expr,
      $.term,
    ),
    bitwise_or: $ => prec.left(PREC.pipe, seq($.bitwise_xor, repeat(seq('|', $.bitwise_xor)))),
    bitwise_xor: $ => prec.left(PREC.xor, seq($.bitwise_and, repeat(seq('^', $.bitwise_and)))),
    bitwise_and: $ => prec.left(PREC.ampersand, seq($.shift_expr, repeat(seq('&', $.shift_expr)))),
    shift_expr: $ => prec.left(PREC.shift, seq($.term, repeat(seq(choice('<<', '>>'), $.term)))),
    term: $ => prec.left(PREC.term, seq($.factor, repeat(seq(choice('*', '/', '//', '%', '@'), $.factor)))),
    factor: $ => prec(PREC.unary_operator, choice(
      seq(choice('+', '-', '~'), $.factor),
      $._power,
    )),
    _power: $ => prec(PREC.power, $.postfix_expression),
    atom: $ => choice(
      $.identifier,
      $.number,
      $.string,
      'sahi', 'galat', 'kuchnahi',
      seq('(', optional(commaSep1($._expression)), ')'),
      seq('[', optional(commaSep1($._expression)), ']'),
      seq('{', optional(commaSep1(choice(seq($._expression, ':', $._expression), $._expression))), '}'),
      seq('{', '}'),
    ),

    postfix_expression: $ => prec.left(PREC.call, choice(
      $.atom,
      seq($.postfix_expression, '[', $.slice, ']'),
      seq($.postfix_expression, '(', optional(commaSep1(choice($.starred_expression, seq($.identifier, '=', $._expression), $._expression))), ')'),
      seq($.postfix_expression, '.', $.identifier),
    )),

    slice: $ => choice(
      seq(optional($._expression), choice(
        seq(':', optional($._expression)),
        seq(':', $._expression, ':', $._expression),
      )),
      $._expression,
    ),

    starred_expression: $ => seq('*', $._expression),

    expression_list: $ => commaSep1($._expression),

    _target_list: $ => choice(
      $.postfix_expression,
      $.unpack_tuple,
      $.star_target_list,
    ),
    unpack_tuple: $ => seq(choice('(', '['), $.target_list_body, choice(')', ']')),
    target_list_body: $ => commaSep1(choice($._expression, seq('*', $._expression))),
    star_target_list: $ => prec.left(seq(seq('*', $.postfix_expression), repeat(seq(',', choice($.postfix_expression, $.unpack_tuple, seq('*', $._expression)))))),


    argument_list: $ => commaSep1(choice(
      $._expression,
      seq($.identifier, '=', $._expression),
      seq('*', $._expression),
      seq('**', $._expression),
    )),

    identifier: $ => /[A-Za-z_][A-Za-z0-9_]*/,
    number: $ => /\d[\d_]*(\.\d[\d_]*)?([eE][+-]?[\d_]+)?[jJ]?|0[xX][0-9a-fA-F_]+[jJ]?|0[bB][01_]+[jJ]?|0[oO][0-7_]+[jJ]?/,
    string: $ => /(f|r|b|fr|rb|br|rf)?(\"\"\"[\s\S]*?\"\"\"|'''[\s\S]*?'''|"(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/,
    comment: $ => /#[^\n]*/,
  },
});

function commaSep1(rule) {
  return seq(rule, repeat(seq(',', rule)), optional(','));
}
function commaJoinRepeat1(rules) {
  return seq(rules[0], repeat(seq(rules[1], rules[0])));
}
