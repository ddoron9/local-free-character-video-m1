# local-free-character-video-m1

Apple Silicon(M1 Pro 32GB)에서 **무료/로컬 우선**으로 캐릭터 기반 짧은 영상을 만드는 최소 파이프라인 실험 레포입니다.

## What is actually tested

이 레포는 말만 정리한 문서가 아니라, 아래 2개를 **실기동**한 로그와 산출물을 포함합니다.

1. **Wan 2.1 GGUF image-to-video quick test**
   - 입력: `results/svd_start.png`
   - 출력: `results/wan_quick_test_rerun.mp4`
   - 환경: ComfyUI + Wan 2.1 I2V 14B 480p GGUF(Q4_K_M)

2. **SDXL Turbo stills -> ffmpeg short-form video**
   - 입력: `results/storyboard_rabbit_space.json`
   - 중간 산출물: `results/anime_stills_rerun/*.png`
   - 출력: `results/final_anime_rerun_fixed.mp4`

## Machine

- MacBook Pro M1 Pro
- Unified Memory: 32GB
- Backend: MPS / Metal

## Rabbit consistency preview

아래 GIF는 토끼 캐릭터로 생성한 5개 장면 클립을 2x3 그리드로 묶은 비교본입니다.  
완전한 identity lock 수준은 아니지만, **귀/얼굴 실루엣/색감/애니메풍 토끼 캐릭터성**이 어느 정도 유지되는지 빠르게 확인할 수 있습니다.

![Rabbit similarity grid](assets/rabbit_similarity_grid.gif)

## Verified results

### A. Wan quick i2v rerun
- wall time: **277.58s**
- max resident set size: **12.59GB**
- peak memory footprint: **57.16GB**
- output: ~0.625s / 5 frames / 480x832 MP4
- note: 종료 시 ComfyUI `ModelPatcher.__del__` 경고가 있었지만 결과 파일은 정상 생성됨

로그: `logs/wan_quick_test_rerun.log`

### B. SDXL Turbo stills rerun
- wall time: **49.43s**
- max resident set size: **754MB**
- peak memory footprint: **14.61GB**
- output: 5 storyboard stills

로그: `logs/anime_stills_rerun.log`

### C. ffmpeg render rerun
- 첫 실행은 **concat path bug로 실패**
- 수정 후 재실행 성공
- fixed rerun wall time: **16.71s**
- output: `results/final_anime_rerun_fixed.mp4`
- final video: **24.0s**, **8.35MB**, 1080x1920

로그:
- 실패: `logs/render_anime_video_rerun.log`
- 성공: `logs/render_anime_video_fixed_rerun.log`

## Repo structure

- `scripts/`: 실험용 스크립트
- `logs/`: 재실행 로그
- `results/`: 샘플 입력/출력/중간 산출물
- `docs/`: 메모와 요약

## Key takeaways

- **M1 Pro 32GB에서도 image-to-video 최소 실험은 가능**하다.
- 다만 **Wan 14B GGUF도 짧은 테스트 기준 수 분 단위**라서, 긴 영상을 바로 뽑기에는 비효율적이다.
- 현실적인 워크플로는:
  1. SDXL Turbo/Lightning 급으로 장면 스틸 생성
  2. 필요한 장면만 짧게 i2v
  3. 나머지는 ffmpeg/편집기로 쇼츠 구성
- 즉, 올인원 장편 생성보다 **shot-based pipeline**이 Apple Silicon에서 훨씬 실용적이다.

## Repro notes

이 레포는 우선 **검증 로그와 산출물 공개**에 초점을 맞췄습니다.

현재 스크립트 중:
- `generate_anime_stills.py`: diffusers 환경에서 재현 가능
- `render_anime_video.py`: 상대경로/concat 버그 수정 반영
- `generate_wan_quick_test.py`: ComfyUI + Wan 모델 파일이 이미 준비된 환경을 전제로 함

## Known issues

- Wan 테스트는 결과가 매우 짧고, 아직 품질 벤치마크라기보다 **구동 확인용**입니다.
- `generate_anime_stills.py` 프롬프트 일부가 CLIP 77 token 제한으로 잘립니다.
- video consistency 자체는 아직 weak baseline 수준입니다.

## Next steps

- character reference 기반 img2img / IP-Adapter 비교
- scene consistency 정량 평가표 추가
- Wan/SVD/AnimateDiff 계열 비교
- M1 Pro 기준 품질-시간 tradeoff 표 정리
