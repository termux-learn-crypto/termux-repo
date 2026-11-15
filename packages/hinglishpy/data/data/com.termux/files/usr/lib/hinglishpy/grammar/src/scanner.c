#include "tree_sitter/array.h"
#include "tree_sitter/parser.h"

#include <stdint.h>
#include <string.h>

enum TokenType { INDENT, DEDENT, NEWLINE };

static inline void advance(TSLexer *lexer) { lexer->advance(lexer, false); }
static inline void skip(TSLexer *lexer) { lexer->advance(lexer, true); }

typedef struct { Array(uint16_t) indents; } Scanner;

bool tree_sitter_hinglishpy_external_scanner_scan(void *payload, TSLexer *lexer, const bool *valid_symbols) {
  Scanner *scanner = (Scanner *)payload;

  lexer->mark_end(lexer);

  bool found_end_of_line = false;
  long indent_length = 0;
  int32_t first_comment_indent_length = -1;

  for (;;) {
    if (lexer->lookahead == '\n') {
      found_end_of_line = true;
      indent_length = 0;
      skip(lexer);
    } else if (lexer->lookahead == ' ') {
      indent_length++;
      skip(lexer);
    } else if (lexer->lookahead == '\r' || lexer->lookahead == '\f') {
      indent_length = 0;
      skip(lexer);
    } else if (lexer->lookahead == '\t') {
      indent_length += 8;
      skip(lexer);
    } else if (lexer->lookahead == '#') {
      if (!found_end_of_line) return false;
      if (first_comment_indent_length == -1) first_comment_indent_length = (int32_t)indent_length;
      while (lexer->lookahead && lexer->lookahead != '\n') lexer->advance(lexer, true);
      skip(lexer);
      indent_length = 0;
    } else if (lexer->eof(lexer)) {
      indent_length = 0;
      found_end_of_line = true;
      break;
    } else {
      break;
    }
  }

  if (found_end_of_line) {
    if (scanner->indents.size > 0) {
      uint16_t current_indent_length = *array_back(&scanner->indents);
      if (valid_symbols[INDENT] && indent_length > current_indent_length) {
        array_push(&scanner->indents, indent_length);
        lexer->result_symbol = INDENT;
        return true;
      }
      if ((valid_symbols[DEDENT] || !valid_symbols[NEWLINE]) && indent_length < current_indent_length
          && first_comment_indent_length < (int32_t)current_indent_length) {
        array_pop(&scanner->indents);
        lexer->result_symbol = DEDENT;
        return true;
      }
    }
    if (valid_symbols[NEWLINE]) {
      lexer->result_symbol = NEWLINE;
      return true;
    }
  }
  return false;
}

uint32_t tree_sitter_hinglishpy_external_scanner_serialize(void *payload, char *buffer) {
  Scanner *scanner = (Scanner *)payload;
  uint32_t size = 0;
  for (uint32_t i = 1; i < scanner->indents.size && size < TREE_SITTER_SERIALIZATION_BUFFER_SIZE; ++i) {
    uint16_t v = *array_get(&scanner->indents, i);
    buffer[size++] = (char)(v & 0xFF);
    buffer[size++] = (char)((v >> 8) & 0xFF);
  }
  return size;
}

void tree_sitter_hinglishpy_external_scanner_deserialize(void *payload, const char *buffer, uint32_t length) {
  Scanner *scanner = (Scanner *)payload;
  array_delete(&scanner->indents);
  array_push(&scanner->indents, 0);
  for (uint32_t i = 0; i + 1 < length; i += 2) {
    uint16_t v = (unsigned char)buffer[i] | ((unsigned char)buffer[i + 1] << 8);
    array_push(&scanner->indents, v);
  }
}

void *tree_sitter_hinglishpy_external_scanner_create() {
  Scanner *scanner = calloc(1, sizeof(Scanner));
  array_init(&scanner->indents);
  array_push(&scanner->indents, 0);
  return scanner;
}

void tree_sitter_hinglishpy_external_scanner_destroy(void *payload) {
  Scanner *scanner = (Scanner *)payload;
  array_delete(&scanner->indents);
  free(scanner);
}
