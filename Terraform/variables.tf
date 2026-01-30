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
variable "ssh_public_key" {
    type = string
}