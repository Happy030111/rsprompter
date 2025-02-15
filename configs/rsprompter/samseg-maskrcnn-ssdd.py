_base_ = ['_base_/samseg-maskrcnn.py']

work_dir = './work_dirs/rsprompter/samseg-maskrcnn-ssdd'

default_hooks = dict(
    timer=dict(type='IterTimerHook'),
    logger=dict(type='LoggerHook', interval=10),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(type='CheckpointHook', interval=1, max_keep_ckpts=4, save_best='coco/bbox_mAP', rule='greater', save_last=True),
    sampler_seed=dict(type='DistSamplerSeedHook'),
    # visualization=dict(type='DetVisualizationHook', draw=True, interval=1, test_out_dir='vis_data')
)

vis_backends = [dict(type='LocalVisBackend'),
                dict(type='WandbVisBackend', init_kwargs=dict(project='rsprompter-ssdd', group='samseg-maskrcnn', name='samseg-maskrcnn-ssdd'))
                ]
visualizer = dict(
    type='DetLocalVisualizer', vis_backends=vis_backends, name='visualizer')

num_classes = 1

hf_sam_pretrain_name = "work_dirs/sam_cache/sam_vit_base"
# huggingface model name, e.g. facebook/sam-vit-base
# or local repo path, e.g. work_dirs/sam_cache/sam_vit_base
hf_sam_pretrain_ckpt_path = "work_dirs/sam_cache/sam_vit_base/pytorch_model.bin"
# # sam large model
# hf_sam_pretrain_name = "facebook/sam-vit-large"
# hf_sam_pretrain_ckpt_path = "~/.cache//huggingface/hub/models--facebook--sam-vit-large/snapshots/70009d56dac23ebb3265377257158b1d6ed4c802/pytorch_model.bin"
# # sam huge model
# hf_sam_pretrain_name = "facebook/sam-vit-huge"
# hf_sam_pretrain_ckpt_path = "~/.cache/huggingface/hub/models--facebook--sam-vit-huge/snapshots/89080d6dcd9a900ebd712b13ff83ecf6f072e798/pytorch_model.bin"

model = dict(
    type='SAMSegMaskRCNN',
    backbone=dict(
        hf_pretrain_name=hf_sam_pretrain_name,
        init_cfg=dict(type='Pretrained', checkpoint=hf_sam_pretrain_ckpt_path)),
    neck=dict(
        feature_aggregator=dict(
            in_channels=hf_sam_pretrain_name,
            hidden_channels=32,
            select_layers=range(1, 13, 2),
            #### should be changed when using different pretrain model, base: range(1, 13, 2), large: range(1, 25, 2), huge: range(1, 33, 2)
        ),
    ),
    roi_head=dict(
        bbox_head=dict(
            num_classes=num_classes
        ),
        mask_head=dict(
            num_classes=num_classes
        ),
    ),
)

dataset_type = 'SSDDInsSegDataset'

#### should be changed align with your code root and data root
code_root = '/mnt/home/xx/codes/RSPrompter'
data_root = '/mnt/home/xx/data/SSDD'

batch_size_per_gpu = 2
num_workers = 8
persistent_workers = True
train_dataloader = dict(
    batch_size=batch_size_per_gpu,
    num_workers=num_workers,
    persistent_workers=persistent_workers,
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file=code_root + '/data/SSDD/annotations/SSDD_instances_train.json',
        data_prefix=dict(img='imgs'),
    )
)

val_dataloader = dict(
    batch_size=batch_size_per_gpu,
    num_workers=num_workers,
    persistent_workers=persistent_workers,
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file=code_root + '/data/SSDD/annotations/SSDD_instances_val.json',
        data_prefix=dict(img='imgs'),
    )
)

find_unused_parameters = True
test_dataloader = val_dataloader
resume = False
load_from = None

base_lr = 0.0002
max_epochs = 250
train_cfg = dict(max_epochs=max_epochs)

param_scheduler = [
    dict(
        type='LinearLR', start_factor=0.001, by_epoch=False, begin=0, end=50),
    dict(
        type='CosineAnnealingLR',
        eta_min=base_lr * 0.001,
        begin=1,
        end=max_epochs,
        T_max=max_epochs,
        by_epoch=True
    )
]

optim_wrapper = dict(
    type='AmpOptimWrapper',
    dtype='float16',
    optimizer=dict(
        type='AdamW',
        lr=base_lr,
        weight_decay=0.05
    )
)