#pragma once

#include <stddef.h>
#include <string.h>

inline bool metadataContainsExactToken(const char* metadata, const char* token) {
  const size_t tokenLength = strlen(token);
  const char* match = strstr(metadata, token);
  while (match != nullptr) {
    const char next = match[tokenLength];
    if (next == ',' || next == '}') {
      return true;
    }
    match = strstr(match + 1, token);
  }
  return false;
}
