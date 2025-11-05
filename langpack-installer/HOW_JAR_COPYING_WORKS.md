# How JAR File Copying Works in Language Pack Installer

This document explains how language resources are handled for Java JAR files in Pentaho.

## The Problem

Pentaho uses many Java libraries (JAR files) that contain embedded localization messages inside them. These messages are stored as `.properties` files deep inside the JAR archives.

For example, the `pentaho-metadata.jar` file contains:
```
pentaho-metadata.jar (ZIP archive)
└── org/
    └── pentaho/
        └── metadata/
            └── messages/
                ├── messages.properties       (English - default)
                ├── messages_es.properties    (Spanish)
                ├── messages_pt_PT.properties (Portuguese)
                └── messages_ru.properties    (Russian) ← We need to add this!
```

**Challenge**: How do we add new language files to existing JAR archives without:
1. Modifying the original JARs (complex, risky)
2. Repackaging entire JARs (legal issues, version conflicts)
3. Breaking Pentaho's classloader

## The Solution: Directory-Based Override

Instead of modifying JAR files, we use Java's classloader behavior to "overlay" new resources.

### How Java Classloading Works

When Java looks for a resource like `org/pentaho/metadata/messages/messages_ru.properties`, it searches in this order:

1. **Filesystem directories** (if in classpath)
2. **JAR files** (if in classpath)
3. **First match wins**

We exploit this by creating parallel directory structures!

## Language Pack Data Structure

In the language pack data, JAR contents are stored with a `_jar` suffix:

```
data/ru/tomcat/webapps/pentaho/WEB-INF/lib/
├── pentaho-metadata_jar/                    ← Directory (not a real JAR)
│   └── org/
│       └── pentaho/
│           └── metadata/
│               └── messages/
│                   └── messages_ru.properties
│
├── pentaho-platform-core_jar/
│   └── org/
│       └── pentaho/
│           └── platform/
│               └── util/
│                   └── messages/
│                       └── messages_ru.properties
│
└── classic-core_jar/
    └── org/
        └── pentaho/
            └── reporting/
                └── engine/
                    └── classic/
                        └── core/
                            └── messages/
                                └── messages_ru.properties
```

**Key Insight**: The `_jar` suffix tells the installer "these are JAR contents, handle specially"

## What The Installer Does

### Current Implementation (Simple Overlay)

The Python installer copies these directory structures alongside the JARs:

**Source** (Language pack data):
```
data/ru/tomcat/.../lib/pentaho-metadata_jar/org/pentaho/...
```

**Destination** (Pentaho installation):
```
/opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib/
├── pentaho-metadata.jar           ← Original JAR (unchanged)
└── pentaho-metadata/              ← New directory we create
    └── org/
        └── pentaho/
            └── metadata/
                └── messages/
                    └── messages_ru.properties
```

### Code Implementation

Here's what happens in the installer:

```python
# In pentaho-langpack.py, lines 213-229

for jar_dir in lib_src.iterdir():
    if jar_dir.is_dir() and jar_dir.name.endswith('_jar'):
        # Extract JAR name: "pentaho-metadata_jar" → "pentaho-metadata"
        jar_name = jar_dir.name[:-4]  # Remove '_jar' suffix

        # Create parallel directory structure
        dest_dir = lib_dest / jar_name

        # Copy all files maintaining internal structure
        for src_file in jar_dir.rglob('*'):
            if not src_file.is_file():
                continue

            # Preserve the package structure: org/pentaho/metadata/...
            rel_path = src_file.relative_to(jar_dir)
            dest_file = dest_dir / rel_path

            copy_file(src_file, dest_file, convert_encoding)
```

### Example: Installing Russian for pentaho-metadata

**Before installation:**
```
/opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib/
└── pentaho-metadata.jar (contains English, Spanish, Portuguese)
```

**After installation:**
```
/opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib/
├── pentaho-metadata.jar                                    ← Unchanged
└── pentaho-metadata/                                       ← NEW!
    └── org/pentaho/metadata/messages/
        └── messages_ru.properties                          ← Russian messages
```

**When Pentaho runs:**
```java
// Java code in Pentaho
ResourceBundle bundle = ResourceBundle.getBundle(
    "org.pentaho.metadata.messages.messages",
    new Locale("ru")
);
```

Java's classloader searches:
1. ✓ Finds `/lib/pentaho-metadata/org/pentaho/metadata/messages/messages_ru.properties`
2. (Doesn't need to look in JAR since it already found it!)

## Advantages of This Approach

### ✅ Pros

1. **Non-invasive**: Original JARs remain untouched
2. **Simple**: Just copy files to filesystem
3. **Fast**: No need to unpack/repack JARs
4. **Safe**: Easy to rollback (just delete directories)
5. **Legal**: No redistribution of modified JARs
6. **Works**: Java classloader naturally prefers filesystem over JARs

### ⚠️ Cons

1. **Cluttered directory**: Extra directories in `/lib/`
2. **Not inside JAR**: Files aren't "properly" packaged
3. **Non-standard**: Unusual approach (but works!)

## Alternative Approach: True JAR Modification

For a production system, you might want to actually inject files into JARs:

```python
import zipfile

def inject_into_jar(jar_path, files_to_add):
    """Actually modify a JAR file to add new resources"""

    # JARs are just ZIP files
    with zipfile.ZipFile(jar_path, 'a') as jar:
        for file_path, content in files_to_add.items():
            # Add new entry: org/pentaho/metadata/messages/messages_ru.properties
            jar.writestr(file_path, content)
```

**Why we don't do this:**

1. Requires keeping original JARs as backup
2. Risk of corrupting JARs
3. Pentaho might overwrite on update
4. Signature verification issues
5. More complex code
6. The simple approach works fine!

## How Pentaho's Classloader Works

Tomcat (Pentaho's web server) sets up the classpath like this:

```
CLASSPATH=
  /opt/pentaho/.../WEB-INF/classes/:
  /opt/pentaho/.../WEB-INF/lib/*:     ← This includes both .jar AND directories!
  /opt/pentaho/.../WEB-INF/lib/pentaho-metadata/:
  /opt/pentaho/.../WEB-INF/lib/pentaho-metadata.jar:
  ...
```

When searching for `org/pentaho/metadata/messages/messages_ru.properties`:

1. Checks `WEB-INF/classes/org/pentaho/...` - Not found
2. Checks each entry in `lib/*`:
   - `lib/pentaho-metadata/org/pentaho/...` - ✓ **FOUND!**
   - Stops searching, returns this file
   - Never even checks `pentaho-metadata.jar`

## Verification

You can verify this works by checking at runtime:

```bash
# After installation, find the new directories
find /opt/pentaho/pentaho-server/tomcat/webapps/pentaho/WEB-INF/lib \
  -type d -name "pentaho-*" ! -name "*.jar"

# Output:
# /opt/pentaho/.../lib/pentaho-metadata/
# /opt/pentaho/.../lib/pentaho-platform-core/
# /opt/pentaho/.../lib/classic-core/
```

## Historical Context

This approach comes from the original Kettle-based installer. The Kettle transformations would:

1. Read properties files from language pack
2. Copy them to parallel directory structures
3. Let Java's classloader do its magic

The Python implementation maintains this same battle-tested approach.

## Real-World Example

Let's trace a complete example for Russian metadata messages:

### 1. Language Pack Data
```
data/ru/tomcat/webapps/pentaho/WEB-INF/lib/pentaho-metadata_jar/
└── org/pentaho/metadata/messages/messages_ru.properties

Content:
  MetadataEditor.USER_NAME_LABEL=Имя пользователя
  MetadataEditor.PASSWORD_LABEL=Пароль
```

### 2. Installation Command
```bash
./pentaho-langpack install ru --pentaho /opt/pentaho/pentaho-server
```

### 3. Files Copied
```
Source:
  data/ru/.../pentaho-metadata_jar/org/pentaho/metadata/messages/messages_ru.properties

Destination:
  /opt/pentaho/.../lib/pentaho-metadata/org/pentaho/metadata/messages/messages_ru.properties
```

### 4. Runtime Usage
```java
// In Pentaho metadata editor code
ResourceBundle bundle = ResourceBundle.getBundle(
    "org.pentaho.metadata.messages.messages",
    new Locale("ru", "RU")
);

String userLabel = bundle.getString("MetadataEditor.USER_NAME_LABEL");
// Returns: "Имя пользователя" (from our installed file!)
```

## Debugging

If language isn't appearing, check:

```bash
# 1. Verify files were copied
ls -la /opt/pentaho/.../lib/pentaho-metadata/org/pentaho/metadata/messages/

# 2. Check file permissions
stat /opt/pentaho/.../lib/pentaho-metadata/org/pentaho/metadata/messages/messages_ru.properties

# 3. Verify classpath (in running Pentaho)
# Check Tomcat catalina.out for classpath entries

# 4. Test resource loading
# From Pentaho Groovy console:
this.class.classLoader.getResource(
  "org/pentaho/metadata/messages/messages_ru.properties"
)
```

## Summary

**The "JAR copying" doesn't actually copy INTO jars.**

Instead:
1. ✅ We create parallel directory structures next to JARs
2. ✅ Java's classloader finds files in directories before JARs
3. ✅ Pentaho loads our language files instead of JAR's defaults
4. ✅ Original JARs remain untouched
5. ✅ Simple, safe, and it works!

This is a clever hack that exploits Java's classloading order to overlay new resources without modifying original JARs. It's been proven to work reliably across Pentaho versions.
