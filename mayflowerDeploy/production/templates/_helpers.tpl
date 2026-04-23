{{- define "ui-testing-tool.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version | replace "+" "_" }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: ui-testing-tool
{{- end -}}

{{/*
Check if a values entry should be tracked by image updater
(has image with tag "latest" and not a local registry)
*/}}
{{- define "ui-testing-tool.isImageUpdated" -}}
{{- if and (kindIs "map" .config) (hasKey .config "image") -}}
{{- $img := index .config "image" -}}
{{- if and (hasPrefix "latest" ($img.tag | default "")) (not (hasPrefix "localhost" ($img.repository | default ""))) -}}true{{- end -}}
{{- end -}}
{{- end -}}
