{{- define "rook.name" -}}
rook-sample-app
{{- end }}
{{- define "rook.fullname" -}}
{{ include "rook.name" . }}
{{- end }}
