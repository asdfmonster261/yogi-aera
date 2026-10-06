from patch import BaseSubPatch


class SubPatch(BaseSubPatch):
    def __init__(self, manager):
        super().__init__(manager)
        self.name = "aeraui: take plugins from our forks of AERA's catalog"
        self.target_file = "bootable/recovery/aeraui/features/plugins/plugin_manager.cpp"

        self.CHANGES = [
            (
                r"""
constexpr char kCatalogUrl[] =
    "https://raw.githubusercontent.com/AERA-Plugins/registry/main/catalog.json";
constexpr char kCatalogSignatureUrl[] =
    "https://raw.githubusercontent.com/AERA-Plugins/registry/main/catalog.json.sig";
""",
                r"""
// Our fork of AERA's registry, which serves the plugins from our forks of them.
constexpr char kCatalogUrl[] =
    "https://raw.githubusercontent.com/asdfmonster261/aera-plugin-registry/main/catalog.json";
constexpr char kCatalogSignatureUrl[] =
    "https://raw.githubusercontent.com/asdfmonster261/aera-plugin-registry/main/catalog.json.sig";
"""
            ),
            (
                r"""
    0x5e, 0xed, 0xad, 0x08, 0x6e, 0x48, 0x73, 0xe9,
}};
""",
                r"""
    0x5e, 0xed, 0xad, 0x08, 0x6e, 0x48, 0x73, 0xe9,
}};
// Signs our catalog and the plugins we change. AERA's key above still verifies the
// plugins our forks carry unchanged.
constexpr std::array<uint8_t, 32> kOwnSigningKey{{
    0xfe, 0xac, 0x7e, 0x71, 0x0d, 0xf4, 0x56, 0xb2,
    0x12, 0xa9, 0xf4, 0x08, 0x23, 0x08, 0x68, 0xbe,
    0xfc, 0x7c, 0xd9, 0x23, 0x80, 0x01, 0xa7, 0x01,
    0x9b, 0x08, 0xc6, 0x01, 0x74, 0xaa, 0x9b, 0x58,
}};
"""
            ),
            (
                r"""
bool OfficialUrl(const std::string &url) {
  constexpr char raw[] = "https://raw.githubusercontent.com/AERA-Plugins/";
  constexpr char github[] = "https://github.com/AERA-Plugins/";
  return url.compare(0, sizeof(raw) - 1, raw) == 0 ||
         url.compare(0, sizeof(github) - 1, github) == 0;
}
""",
                r"""
bool OfficialUrl(const std::string &url) {
  // Our forks serve everything. AERA's own URLs stay allowed because the manifests
  // the forks carry unchanged still name them.
  static const char *const kPrefixes[] = {
      "https://raw.githubusercontent.com/asdfmonster261/aera-plugin-",
      "https://github.com/asdfmonster261/aera-plugin-",
      "https://raw.githubusercontent.com/AERA-Plugins/",
      "https://github.com/AERA-Plugins/",
  };
  for (const char *prefix : kPrefixes)
    if (url.rfind(prefix, 0) == 0) return true;
  return false;
}
"""
            ),
            (
                r"""
bool Verify(const std::string &content, const std::string &signature_text) {
  std::array<uint8_t, 64> signature{};
  if (!DecodeSignature(signature_text, signature)) return false;
  EVP_PKEY *key = EVP_PKEY_new_raw_public_key(
      EVP_PKEY_ED25519, nullptr, kSigningKey.data(), kSigningKey.size());
""",
                r"""
bool VerifyWith(const std::string &content, const std::array<uint8_t, 64> &signature,
                const std::array<uint8_t, 32> &public_key) {
  EVP_PKEY *key = EVP_PKEY_new_raw_public_key(
      EVP_PKEY_ED25519, nullptr, public_key.data(), public_key.size());
"""
            ),
            (
                r"""
  EVP_MD_CTX_free(context);
  EVP_PKEY_free(key);
  return valid;
}
""",
                r"""
  EVP_MD_CTX_free(context);
  EVP_PKEY_free(key);
  return valid;
}

bool Verify(const std::string &content, const std::string &signature_text) {
  std::array<uint8_t, 64> signature{};
  if (!DecodeSignature(signature_text, signature)) return false;
  return VerifyWith(content, signature, kSigningKey) ||
         VerifyWith(content, signature, kOwnSigningKey);
}
"""
            ),
            (
                r"""
    gCatalog = parsed; return parsed;
  }
  return {BrowserFallback()};
}
""",
                r"""
    gCatalog = parsed; return parsed;
  }
  // No catalog fetched yet: nothing to offer, rather than AERA's browser.
  return {};
}
"""
            ),
        ]
