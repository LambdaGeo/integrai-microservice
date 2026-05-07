import csv
from django.core.management.base import BaseCommand
# DESABILITADO: Modelos migrados para microservice gestantes-service
# from apps.gestantes.models import Avaliacao, Pilula

class Command(BaseCommand):
    help = 'Exports Avaliacao and Pilula data to CSV files (DESABILITADO - use microservice API)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Este comando foi desabilitado. Use a API do microservice gestantes-service ao invés.'))

        # Export Avaliacoes
        with open('avaliacoes.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'data_aplicacao', 'peso_atual', 'idade_gestacional',
                'consultas_prenatal', 'corrimento_vaginal', 'periodontite_carie',
                'hipertensao_gestacao', 'diabetes_gestacao', 'estresse_gestacao',
                'historico_familiar_alergia', 'consumo_bebidas_adocadas',
                'consumo_ultraprocessados', 'consumo_alcool', 'fumante_gestacao',
                'prob_asma', 'prob_carie', 'prob_alergia', 'prob_obesidade',
                'prob_integralidade', 'top_fatores', 'status_processamento_llm',
                'llm_sintese'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for avaliacao in Avaliacao.objects.all():
                resultado = avaliacao.resultado_integralidade_saude or {}
                top_fatores = '_'.join(resultado.get('top_fatores', []))

                writer.writerow({
                    'id': avaliacao.id,
                    'data_aplicacao': avaliacao.data_aplicacao,
                    'peso_atual': avaliacao.peso_atual,
                    'idade_gestacional': avaliacao.idade_gestacional,
                    'consultas_prenatal': avaliacao.consultas_prenatal,
                    'corrimento_vaginal': avaliacao.corrimento_vaginal,
                    'periodontite_carie': avaliacao.periodontite_carie,
                    'hipertensao_gestacao': avaliacao.hipertensao_gestacao,
                    'diabetes_gestacao': avaliacao.diabetes_gestacao,
                    'estresse_gestacao': avaliacao.estresse_gestacao,
                    'historico_familiar_alergia': avaliacao.historico_familiar_alergia,
                    'consumo_bebidas_adocadas': avaliacao.consumo_bebidas_adocadas,
                    'consumo_ultraprocessados': avaliacao.consumo_ultraprocessados,
                    'consumo_alcool': avaliacao.consumo_alcool,
                    'fumante_gestacao': avaliacao.fumante_gestacao,
                    'prob_asma': resultado.get('prob_asma'),
                    'prob_carie': resultado.get('prob_carie'),
                    'prob_alergia': resultado.get('prob_alergia'),
                    'prob_obesidade': resultado.get('prob_obesidade'),
                    'prob_integralidade': resultado.get('prob_integralidade'),
                    'top_fatores': top_fatores,
                    'status_processamento_llm': avaliacao.status_processamento_llm,
                    'llm_sintese': avaliacao.llm_sintese
                })

        self.stdout.write(self.style.SUCCESS('Successfully exported Avaliacoes to avaliacoes.csv'))

        # Export Pilulas
        with open('pilulas.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id', 'avaliacao_id', 'titulo', 'conteudo', 'semana_num',
                'data_geracao', 'data_envio', 'status'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for pilula in Pilula.objects.all():
                writer.writerow({
                    'id': pilula.id,
                    'avaliacao_id': pilula.avaliacao.id,
                    'titulo': pilula.titulo,
                    'conteudo': pilula.conteudo,
                    'semana_num': pilula.semana_num,
                    'data_geracao': pilula.data_geracao,
                    'data_envio': pilula.data_envio,
                    'status': pilula.status
                })

        self.stdout.write(self.style.SUCCESS('Successfully exported Pilulas to pilulas.csv'))
