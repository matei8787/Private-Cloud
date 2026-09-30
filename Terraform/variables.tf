variable "pxm_url" {
    type = string
}
variable "pxm_token_id" {
    type = string
}
variable "pxm_token_secret" {
    type = string
    sensitive = true
}
variable "pxm_insecure" {
    description = "Skip TLS verification against the Proxmox API. Keep false unless the API is still on a self-signed certificate."
    type = bool
    default = false
}
variable "ssh_public_key" {
    type = string
}