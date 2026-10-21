"""Configurações de ambiente para Next.js."""
import { loadEnvConfig } from '@next/env'
import path from 'path'

const projectDir = path.resolve(__dirname, '../../..')
loadEnvConfig(projectDir)
