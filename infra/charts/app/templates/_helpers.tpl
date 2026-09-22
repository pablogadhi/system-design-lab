{{- define "app.name" -}}{{ .Release.Name }}{{- end -}}

{{- define "app.labels" -}}
app.kubernetes.io/name: {{ .Release.Name }}
app.kubernetes.io/part-of: sdl
{{- end -}}

{{- define "app.selector" -}}
app.kubernetes.io/name: {{ .Release.Name }}
{{- end -}}

{{- define "app.env" -}}
- name: SERVICE_NAME
  value: {{ .Release.Name | quote }}
- name: POD_NAME
  valueFrom: { fieldRef: { fieldPath: metadata.name } }
- name: NODE_NAME
  valueFrom: { fieldRef: { fieldPath: spec.nodeName } }
- name: PORT
  value: {{ .Values.port | quote }}
{{- if and .Values.route.enabled .Values.route.stripPrefix .Values.route.pathPrefix }}
- name: ROOT_PATH
  value: {{ .Values.route.pathPrefix | quote }}
{{- end }}
{{- range $k, $v := .Values.env }}
- name: {{ $k }}
  value: {{ $v | quote }}
{{- end }}
{{- end -}}

{{- define "app.envFrom" -}}
{{- range .Values.connections }}
- prefix: {{ printf "%s_" (. | upper | replace "-" "_") }}
  secretRef:
    name: {{ printf "%s-conn" . }}
{{- end }}
{{- end -}}
