using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json.Linq;
using UnityEditor;
using UnityEditor.PackageManager;
using UnityEngine;
using UnityCliBridge.Tools;
using PackageInfo = UnityEditor.PackageManager.PackageInfo;

namespace UnityCliBridge.Compatibility
{
    /// <summary>Small Editor-only additions using Unity 2023 public APIs.</summary>
    public static class Unity2023Tools
    {
        public enum UndoAction { Undo, Redo }

        [UnityCliTool("unity2023_capabilities", Mutating = false,
            Description = "Read the actual Editor/project/package baseline. Declared capabilities are not runtime test results.")]
        public static object Capabilities()
        {
            var packages = PackageInfo.GetAllRegisteredPackages();
            var bridge = PackageInfo.FindForAssembly(typeof(Unity2023Tools).Assembly);
            var input = packages.FirstOrDefault(p => p.name == "com.unity.inputsystem");
            return new
            {
                projectPath = Path.GetFullPath(Path.GetDirectoryName(Application.dataPath)),
                unityVersion = Application.unityVersion,
                bridgeVersion = bridge?.version,
                adaptation = "unity2023-portable-r1",
                editorOnly = true,
                inputSystemVersion = input?.version,
                isPlaying = EditorApplication.isPlaying,
                isPaused = EditorApplication.isPaused,
                isCompiling = EditorApplication.isCompiling,
                optionalPackages = new
                {
                    addressables = Has(packages, "com.unity.addressables"),
                    timeline = Has(packages, "com.unity.timeline"),
                    recorder = Has(packages, "com.unity.recorder"),
                    visualEffectGraph = Has(packages, "com.unity.visualeffectgraph"),
                    testFramework = Has(packages, "com.unity.test-framework")
                },
                packages = packages.Select(p => new { p.name, p.version, source = p.source.ToString() }).ToArray(),
                limitations = new[]
                {
                    "Optional package tools require the matching installed package and backend.",
                    "Editor operations and eval timeouts do not imply cancellation; never blindly retry a write.",
                    "Instance IDs and Undo history belong to the current Editor session.",
                    "Input automation targets the Input System; it does not simulate physical OS input."
                }
            };
        }

        private static bool Has(PackageInfo[] packages, string name) => packages.Any(p => p.name == name);

        [UnityCliTool("unity2023_undo", Description = "Undo or redo one Editor transaction. No automatic retry; history belongs to this Editor session.")]
        public static object ApplyUndo(UndoAction action)
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode || EditorApplication.isCompiling)
                throw new InvalidOperationException("Undo/redo requires a stable Edit Mode.");
            var before = Undo.GetCurrentGroupName();
            if (action == UndoAction.Undo) Undo.PerformUndo();
            else Undo.PerformRedo();
            return new { action = action.ToString(), previousGroup = before, currentGroup = Undo.GetCurrentGroupName() };
        }

        [UnityCliTool("unity2023_serialized_properties", Mutating = false,
            Description = "Inspect serialized paths, arrays and object references by current-session instanceId. Values are read only.")]
        public static object SerializedProperties(int instanceId, string rootProperty = "", int maxProperties = 256)
        {
            if (maxProperties < 1 || maxProperties > 4096) throw new ArgumentOutOfRangeException(nameof(maxProperties));
            var target = EditorUtility.InstanceIDToObject(instanceId);
            if (target == null) throw new ArgumentException("No object with that instanceId in this Editor session.");
            var rows = new JArray();
            var truncated = false;
            using (var serialized = new SerializedObject(target))
            {
                var iterator = string.IsNullOrEmpty(rootProperty) ? serialized.GetIterator() : serialized.FindProperty(rootProperty);
                if (iterator == null) throw new ArgumentException("Serialized root property does not exist.");
                var depth = iterator.depth;
                var first = true;
                var enterChildren = true;
                var references = new HashSet<long>();
                while (true)
                {
                    if (!(first && !string.IsNullOrEmpty(rootProperty)))
                    {
                        if (!iterator.Next(enterChildren)) break;
                        if (!string.IsNullOrEmpty(rootProperty) && iterator.depth <= depth) break;
                    }
                    first = false;
                    enterChildren = true;
                    if (rows.Count >= maxProperties) { truncated = true; break; }
                    var row = new JObject
                    {
                        ["path"] = iterator.propertyPath,
                        ["type"] = iterator.propertyType.ToString(),
                        ["editable"] = iterator.editable,
                        ["isArray"] = iterator.isArray
                    };
                    if (iterator.isArray) row["arraySize"] = iterator.arraySize;
                    switch (iterator.propertyType)
                    {
                        case SerializedPropertyType.Integer: row["value"] = iterator.longValue; break;
                        case SerializedPropertyType.Boolean: row["value"] = iterator.boolValue; break;
                        case SerializedPropertyType.Float: row["value"] = iterator.doubleValue; break;
                        case SerializedPropertyType.String: row["value"] = iterator.stringValue; break;
                        case SerializedPropertyType.Enum: row["value"] = iterator.enumValueIndex; break;
                        case SerializedPropertyType.ObjectReference:
                            row["instanceId"] = iterator.objectReferenceInstanceIDValue;
                            row["assetPath"] = AssetDatabase.GetAssetPath(iterator.objectReferenceValue);
                            break;
                        case SerializedPropertyType.ManagedReference:
                            // Do not recursively re-enter a SerializeReference cycle.
                            enterChildren = references.Add(iterator.managedReferenceId);
                            break;
                    }
                    rows.Add(row);
                }
            }
            return new { instanceId, objectName = target.name, objectType = target.GetType().FullName, properties = rows, truncated };
        }
    }
}
